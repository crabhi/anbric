import os
from pathlib import Path
import sys

import mitogen
import mitogen.core
import mitogen.master
import mitogen.utils
from ansible_mitogen.target import run_module

from fabfab.core import command

keys_path = Path(__file__).parent.parent / 'test/docker'
my_key = str(keys_path / 'test_key')


def main():
    mitogen.utils.log_to_file(level='DEBUG' if '-v' in sys.argv else 'INFO')

    broker = mitogen.master.Broker()
    router = mitogen.master.Router(broker)

    os.chmod(my_key, 0o600)

    try:
        z = router.ssh(hostname='127.0.1.1', username='user',
                       identity_file=my_key,
                       #check_host_keys='accept',
                       ssh_args=['-o', f'UserKnownHostsFile={keys_path / "known_hosts"}'],
                       python_path='python3')
        print(z)
        print("AAAAAAA", command(z, 'hostname').res['stdout'])
        print("AAAAAAA", command(z, 'hostname'))
        print("AAAAAAA", command(z, 'hostname'))
        print("AAAAAAA", command(z, 'hostname'))

    finally:
        broker.shutdown()


def run_ansible_in_context(c, module_name, module_args):
    import importlib
    m = importlib.import_module(module_name)

    kwargs = {
        'module_map': {'custom': [], 'builtin': []},
        'runner_name': 'NewStyleRunner',
        'service_context': c,
        'py_module_name': module_name,
        'interpreter_fragment': '/usr/bin/python',
        'is_python': True,
        'path': m.__file__,
        'module': module_name,
        'json_args': '{"_raw_params": "hostname"}',
        'good_temp_dir': '/home/user/.ansible/tmp',
    }
    return run_module(kwargs)


if __name__ == "__main__":
    main()
