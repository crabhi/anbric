from ..ansible import ansible_module, _execute
from ..core import task


@task
def command(command_string):
    return _execute('ansible.modules.command', {'_raw_params': command_string})
