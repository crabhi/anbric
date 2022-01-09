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
    def connection_method_name(self) -> str:
        raise NotImplementedError()


@dataclass
class SSHConnection(Connection):
    username: str = None
    hostname: str = None
    port: int = None
    ssh_args: List[str] = None

    def connection_method_name(self) -> str:
        return 'ssh'


@dataclass
class Host:
    connection: Connection


@dataclass
class GroupDefaults:
    connection: Connection
