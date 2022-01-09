import logging

from anbric.ansible.modules import command
from anbric.core import play

LOG = logging.getLogger(__name__)


@play(hosts='all')
def test_play(host):
    LOG.warning("Running at host %s", host.id)
    command('hostname')


if __name__ == '__main__':
    from anbric.cli import anbric_play

    anbric_play()
