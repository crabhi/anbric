from anbric.ansible.modules import command
from anbric.core import play


@play(hosts='all')
def test_play(host):
    print("Running at host", host.id)
    command('hostname')


if __name__ == '__main__':
    from anbric.cli import anbric_play

    anbric_play()
