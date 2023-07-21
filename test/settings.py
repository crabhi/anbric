from pathlib import Path

from anbric.api import Host, SSHConnection, GroupDefaults

PROJECT_DIR = Path(__file__).absolute().parent

HOSTS = {
    'test1': Host(SSHConnection(hostname='127.0.1.1', port=2222)),
    'test2': Host(SSHConnection(hostname='127.0.1.1', port=2223)),
    'test3': Host(SSHConnection(hostname='127.0.1.1', port=2224)),
}

GROUPS = {
    'masters': {'test1'},
    'workers': {'test1', 'test2', 'test3'},
}

GROUP_DEFAULTS = {
    'all': GroupDefaults(SSHConnection(
            username='user',
            ssh_args=["-o", f"UserKnownHostsFile={PROJECT_DIR}/docker/known_hosts",
                      "-o", f"IdentityFile={PROJECT_DIR}/docker/test_key"]
    ))
}
