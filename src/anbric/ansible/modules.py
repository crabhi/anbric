from ..ansible import ansible_module


def command(command_string):
    return ansible_module('ansible.modules.command', {'_raw_params': command_string})

