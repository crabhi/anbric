import os
from pathlib import Path
import sys

import mitogen
import mitogen.utils
from ansible.playbook.task import Task

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
        z.call(os.system, 'hostname')

        from ansible.plugins.loader import action_loader
        t = Task()
        t.name = 'ping'
        print(action_loader.get('ansible.legacy.normal', task=t))
    finally:
        broker.shutdown()


if __name__ == "__main__":
    main()
