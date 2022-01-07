from anbric.ansible.modules import command
from anbric.core import play


@play(hosts='servers')
def test_play(host):
    print("Running at host", host.name)
    command('hostname')

