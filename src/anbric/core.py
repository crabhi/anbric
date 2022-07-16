import importlib
import inspect
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from dataclasses import dataclass
from typing import Dict, List, Any, TypeVar, Generic

import mitogen
import mitogen.master
from mitogen.core import StreamError
from mitogen.parent import Router, Context

from anbric.api import Connection

LOG = logging.getLogger(__name__)
PLAY_MARKER = object()


class UserReadableError(Exception):
    pass


class SelectorDoesntMatch(UserReadableError):
    pass


class AnbricConnectionError(UserReadableError):
    pass


T = TypeVar('T')


@dataclass
class AttrDiff(Generic[T]):
    before: T
    after: T


@dataclass
class Diff:
    lines_diff: str = None
    attrs_diff: dict[str, AttrDiff] = None


@dataclass
class Result:
    task_name: str
    rc: int
    stdout: str
    stderr: str
    msg: str
    changed: bool = None
    error: str = None
    res: dict = None

    def log_result(self, logger):
        if self.rc == 0:
            if self.changed:
                logger.warning('[yellow]TASK %s \\[%s]: changed[/]',
                               self.task_name, Vars.vars['host'].id, extra={'markup': True})
                self.changed_details(logger)
            else:
                logger.warning('[green]TASK %s \\[%s]: ok[/]',
                               self.task_name, Vars.vars['host'].id, extra={'markup': True})
                self.ok_details(logger)
        else:
            logger.warning('[red]TASK %s \\[%s]: error[/]',
                           self.task_name, Vars.vars['host'].id, extra={'markup': True})
            self.error_details(logger)

    def changed_details(self, logger):
        pass

    def ok_details(self, logger):
        pass

    def error_details(self, logger):
        logger.info('%s', self.msg)


class Vars(threading.local):
    context: Context
    vars: Dict[str, Any]
    results: List[Result]


def task(func):
    # Don't wrap in child contexts - recursion trying to call within Vars.context
    if not mitogen.is_master:
        return func

    @wraps(func)
    def wrapper(*args, name=None, **kwargs):
        # TODO _notify
        if name is None:
            name = func.__name__

        received = Vars.context.call(func, *args, **kwargs)

        stdout = json.loads(received['stdout'])
        res = Result(task_name=name, rc=received['rc'],
                     changed=stdout.get('changed', None), res=stdout, stdout=received['stdout'],
                     stderr=received['stderr'], msg=stdout['msg'])
        Vars.results.append(res)
        res.log_result(LOG)

    return wrapper


@dataclass
class InventoryGroup:
    id: str
    hosts: "List[InventoryHost]"


@dataclass
class InventoryHost:
    id: str
    groups: List[InventoryGroup]
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
            self.hosts[host_id] = InventoryHost(host_id, [], {}, host_data.connection)

        for group_id, hosts in settings.GROUPS.items():
            hosts_list = []
            group = InventoryGroup(group_id, hosts_list)
            self.groups[group_id] = group

            for host in hosts:
                # TODO nested groups?
                inv_host = self.hosts[host]
                inv_host.groups.append(group)
                if inv_host not in hosts_list:  # might be slower for large number of hosts
                    hosts_list.append(inv_host)

        for group_id, group_defaults in getattr(settings, 'GROUP_DEFAULTS', {}).items():
            for host in self.get_hosts(group_id):
                if not isinstance(host.connection_method, group_defaults.connection.__class__):
                    continue
                for k, default_v in group_defaults.connection.__dict__.items():
                    if default_v is not None and getattr(host.connection_method, k, None) is None:
                        setattr(host.connection_method, k, default_v)

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
    Vars.results = []
    try:
        Vars.context = router.connect(host.connection_method.connection_method_name(),
                                      **host.connection_method.__dict__)
    except StreamError as e:
        raise AnbricConnectionError(f'Error connecting to {host.id}: {e}')

    try:
        func(**kwargs)
        return Vars.results
    finally:
        Vars.results = []
        Vars.context = None


# TODO jinja templating
# TODO sudo
def play(func=None, *, hosts='all', max_workers=4):
    # noinspection PyShadowingNames
    def wrapper(func):
        @wraps(func)
        def _executable(inventory):
            LOG.warning('Hosts: %s', hosts)
            play_hosts = inventory.get_hosts(hosts)
            LOG.info('Hosts list: %s', [h.id for h in play_hosts])
            Vars.vars = {}

            broker = mitogen.master.Broker()
            router = mitogen.master.Router(broker)

            try:
                tasks = {}
                results = {}
                with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=func.__name__) as executor:
                    for host in play_hosts:
                        tasks[host.id] = executor.submit(play_task, func, router, host)
                    for host_id, host_task in tasks.items():
                        last_exc = None
                        try:
                            results[host_id] = host_task.result()
                        except UserReadableError as e:
                            last_exc = e
                            if logging.root.getEffectiveLevel() <= logging.DEBUG:
                                LOG.exception(f'Exception in play {func.__module__}.{func}', stacklevel=5)
                            else:
                                LOG.error(f'[bold red]{e}[/]', extra={"markup": True})
                    return last_exc is None, results

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
