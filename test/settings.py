from pathlib import Path

from anbric.api import Host, SSHConnection, GroupDefaults

SETTINGS_PATH = Path(__file__).absolute()
HOSTS = {
    'test1': Host(SSHConnection(hostname='127.0.1.1')),
    'test2': Host(SSHConnection(hostname='127.0.1.2')),
    'test3': Host(SSHConnection(hostname='127.0.1.3')),
}

GROUPS = {
    'masters': {'test1'},
    'workers': {'test1', 'test2', 'test3'},
}

GROUP_DEFAULTS = {
    'all': GroupDefaults(SSHConnection(
            username='user',
            ssh_args=["-o", f"UserKnownHostsFile={SETTINGS_PATH}/docker/known_hosts",
                      "-o", f"IdentityFile={SETTINGS_PATH}/docker/test_key"]
    ))
}
