import logging

from anbric.ansible.modules import command
from anbric.core import play
from anbric.modules.file import write_file, copy

LOG = logging.getLogger(__name__)


@play(hosts='all')
def test_play(host):
    LOG.warning("Running at host %s", host.id)
    command('hostname')
    write_file('test.txt', 'ahoj', mode=0o640)
    command('ls -l')
    command('cat test.txt')
    copy(dest='.', src='elk.py')


if __name__ == '__main__':
    from anbric.cli import anbric_play

    anbric_play()
