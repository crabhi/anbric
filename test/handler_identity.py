# coding=utf-8

import os
from pathlib import Path

from fabfab import play, sudo, wait_for
from fabfab.ansible.builtin import copy, template, systemctl, uri, lookup

HERE = os.path.dirname(os.path.abspath(__file__))
CONF_DIR = Path(os.path.join(HERE, 'conf'))


def restart(service):
    def handler():
        systemctl(name=service, state='restarted')
    handler.identity = (restart, service)
    return handler


def _deploy_filebeat_conf(client):
    template(
        src=f'clients/{client}/filebeat.yml',
        dest='/etc/filebeat/filebeat.yml',
        mode=0o644,
        _notify=restart('filebeat'),
    )
