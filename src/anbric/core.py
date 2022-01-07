import inspect
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from dataclasses import dataclass
from typing import Dict, List

import mitogen
import mitogen.master
import toml

PLAY_MARKER = object()


class Vars(threading.local):
    pass


@dataclass
class Result:
    rc: int
    stdout: str
    stderr: str
    changed: bool = None
    error: str = None
    res: dict = None


@dataclass
class Group:
    name: str
    hosts: "List[Host]"
    vars: Dict[str, str]
    connection: Dict[str, str]


@dataclass
class Host:
    name: str
    group: Group
    vars: Dict[str, str]
    connection: Dict[str, str]

    @property
    def ssh_args(self):
        return {'hostname': self.name, 'python_path': 'python3', **self.group.connection, **self.connection}


class Inventory:
    def __init__(self, fname='hosts.toml'):
        with open(fname) as f:
            config = toml.load(f)

        self.groups = {s: Group(
            name=s, hosts=[], vars=val.get('vars', {}), connection=val.get('_connection', {})
        ) for s, val in config.items()}

        for group in self.groups.values():
            for host, host_config in config[group.name].items():
                if host.startswith('_'):
                    continue

                group.hosts.append(Host(
                    name=host, group=group,
                    connection=host_config.get('_connection', {}),
                    vars=host_config.get('vars', {})
                ))

    def get_hosts(self, selector):
        if selector == 'all':
            return self.all_hosts()

        if selector in self.groups:
            return self.groups[selector].hosts

        for h in self.all_hosts():
            if selector == h.name:
                return [h]

        raise ValueError(f'No group or host matches {selector}')  # TODO user-friendly

    def all_hosts(self):
        for g in self.groups.values():
            for h in g.hosts:
                yield h


def play_task(func, router, host):
    Vars.vars['host'] = host

    kwargs = {p: Vars.vars[p] for p in inspect.signature(func).parameters if p in Vars.vars}
    Vars.context = router.ssh(**host.ssh_args)

    try:
        return func(**kwargs)
    finally:
        Vars.context = None


def play(func=None, *, hosts='all', max_workers=4):
    # noinspection PyShadowingNames
    def wrapper(func):
        @wraps(func)
        def _executable(inventory):
            play_hosts = inventory.get_hosts(hosts)
            Vars.vars = {}

            broker = mitogen.master.Broker()
            router = mitogen.master.Router(broker)

            try:
                tasks = []
                with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=func.__name__) as executor:
                    for host in play_hosts:
                        tasks.append(executor.submit(
                            play_task, func, router, host
                        ))
                    for task in tasks:
                        task.result()
            finally:
                Vars.vars = None
                broker.shutdown()

        _executable.anbric_type = PLAY_MARKER
        return _executable

    if func and callable(func):
        return wrapper(func)
    else:
        return wrapper


variables = Vars()
