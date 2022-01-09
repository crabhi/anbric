import importlib
import inspect
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from dataclasses import dataclass
from typing import Dict, List, Any, Set

import mitogen
import mitogen.master
from mitogen.core import StreamError
from mitogen.parent import Router

from anbric.api import Connection, Host

PLAY_MARKER = object()


class Vars(threading.local):
    pass


class UserReadableError(Exception):
    pass


class SelectorDoesntMatch(UserReadableError):
    pass


class AnbricConnectionError(UserReadableError):
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
class InventoryGroup:
    id: str
    hosts: "Set[InventoryHost]"


@dataclass(frozen=True)
class InventoryHost:
    id: str
    groups: Set[InventoryGroup]
    vars: Dict[str, Any]
    connection_method: Connection


class Inventory:
    @staticmethod
    def create(settings_module=None):
        if not settings_module:
            settings_module = os.getenv('ANBRIC_SETTINGS_MODULE', 'settings')

        return Inventory(settings_module)

    def __init__(self, settings_module):
        settings = importlib.import_module(settings_module)  # type: Any

        self.groups = {}
        self.hosts = {}

        if not getattr(settings, 'GROUPS', None):
            settings.GROUPS = {'all': list(settings.HOSTS.keys())}

        for host_id, host_data in settings.HOSTS.items():
            self.hosts[host_id] = InventoryHost(host_id, set(), {}, host_data.connection)

        for group_id, hosts in settings.GROUPS.items():
            hosts_list = set()
            group = InventoryGroup(group_id, hosts_list)
            self.groups[group_id] = group

            for host in hosts:
                # TODO nested groups?
                inv_host = self.hosts[host]
                inv_host.groups.add(group)
                hosts_list.add(inv_host)

    def get_hosts(self, selector):
        if selector == 'all':
            return self.all_hosts()

        if selector in self.groups:
            return self.groups[selector].hosts

        for h in self.all_hosts():
            if selector == h.id:
                return [h]

        raise SelectorDoesntMatch(f'No group or host matches {selector}')

    def all_hosts(self):
        return self.hosts.values()


def play_task(func, router: Router, host: InventoryHost):
    Vars.vars['host'] = host

    kwargs = {p: Vars.vars[p] for p in inspect.signature(func).parameters if p in Vars.vars}
    try:
        Vars.context = router.connect()
    except StreamError as e:
        raise AnbricConnectionError(f'Error connecting to {host.id}: {e}')

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
