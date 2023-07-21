import importlib
import logging
import sys

import click as click
from rich.logging import RichHandler

from anbric.core import Inventory, UserReadableError, PLAY_MARKER

LOG = logging.getLogger(__name__)
LOGGING_SETTINGS = {
    'verbosity': logging.INFO
}


def setup_excepthook():
    existing_excepthook = sys.excepthook

    def handle_exception(exc_type, exc_value, exc_traceback):
        if not issubclass(exc_type, UserReadableError):
            return existing_excepthook(exc_type, exc_value, exc_traceback)

        if logging.root.getEffectiveLevel() <= logging.DEBUG:
            LOG.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        else:
            LOG.error(exc_value)

    sys.excepthook = handle_exception


def setup_logging(loglevel):
    logging.basicConfig(
        level=loglevel, force=True, format="%(message)s", datefmt="[%X]",
        handlers=[
            RichHandler(show_level=False, show_path=False, rich_tracebacks=False)
        ])


@click.command()
@click.option('-i', '--inventory', default='settings')
@click.argument('playbook')
@click.argument('play', required=False)
@click.option('-l', '--loglevel', default='INFO')
def anbric_play(inventory, playbook, play, loglevel):
    setup_excepthook()
    setup_logging(loglevel)

    if '.' not in sys.path:
        sys.path.append('.')

    inventory = Inventory.create(inventory)

    playbook_module = importlib.import_module(playbook)

    if play:
        plays = [play]
    else:
        plays = [play for play, executable
                 in playbook_module.__dict__.items()
                 if getattr(executable, 'anbric_type', None) == PLAY_MARKER]

    for play in plays:
        LOG.info('PLAY %s.%s', playbook, play)
        play_exec = getattr(playbook_module, play)

        # noinspection PyBroadException
        try:
            all_success, results = play_exec(inventory)
            if all_success:
                exit(0)
            else:
                exit(1)
        except Exception:
            LOG.exception(f'Exception in play {playbook}.{play}', stacklevel=5)
            exit(1)


if __name__ == '__main__':
    anbric_play()
