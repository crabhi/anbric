import abc
from abc import ABC
from dataclasses import dataclass
from typing import List, Set

import mitogen.core
import mitogen.parent
import mitogen.ssh


@dataclass
class Connection(ABC):
    python_path: str = 'python3'

    @abc.abstractmethod
    def connect(self, parents: 'Set[Connection]', router: mitogen.parent.Router) -> mitogen.parent.Connection:
        raise NotImplementedError()


@dataclass
class SSHConnection(Connection):
    username: str = None
    hostname: str = None
    port: int = None
    ssh_args: List[str] = None

    def connect(self, parents: 'Set[SSHConnection]', router: mitogen.parent.Router) -> mitogen.ssh.Connection:
        args = {}
        for conn in list(parents) + [self]:
            for k, v in conn.__dict__.items():
                if v is not None:
                    args[k] = v
        return router.ssh(**args)


@dataclass
class Host:
    connection: Connection


@dataclass
class GroupDefaults:
    connection: Connection
