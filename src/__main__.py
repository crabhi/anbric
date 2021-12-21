import os
from pathlib import Path

import mitogen
import mitogen.utils

keys_path = Path(__file__).parent.parent / 'test/docker'


def main():
    mitogen.utils.log_to_file()

    broker = mitogen.master.Broker()
    router = mitogen.master.Router(broker)

    try:
        z = router.ssh(hostname='127.0.1.1', username='user',
                       identity_file=str(keys_path / 'test_key'),
                       check_host_keys='accept',
                       #ssh_args=f'-o UserKnownHostsFile={keys_path / "known_hosts"}',
                       python_path='python3')
        z.call(os.system, 'hostname')
    finally:
        broker.shutdown()


if __name__ == "__main__":
    main()
