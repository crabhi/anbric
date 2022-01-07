import importlib
import sys

import click as click

from anbric.core import Inventory


@click.command()
@click.option('-i', '--inventory', default='hosts.toml', type=click.Path(exists=True))
@click.argument('playbook')
@click.argument('play', required=False, default='main')
def anbric_play(inventory, playbook, play):
    inventory = Inventory(inventory)

    if '.' not in sys.path:
        sys.path.append('.')

    playbook_module = importlib.import_module(playbook)

    play_exec = getattr(playbook_module, play)
    play_exec(inventory)
