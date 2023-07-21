# Anbric

A cross-over between Ansible and Fabric.

### Why

Ansible makes it possible to manage state on many servers. It has its nice parts,
namely idempotent tasks, status reporting, little server-side dependencies.

However, Ansible has its pain points as well. Most notably, you're programming
in YAML. Although Ansible playbook is an imperative script, things like loops
or simple branching are not intuitive and can get complicated quickly. Writing
your own Python task is also not a trivial matter.

Anbric brings Ansible tasks as you know them into a real programming language.
The execution model is very similar to that of Ansible - tasks execute sequentially,
most of them run entirely on the remote server and the play can make choices
based on the returned data

## Status

- [x] Basic commands working.
- [x] Parallel execution
- [x] Diff
- [ ] Import most existing Ansible modules as tasks
- [ ] Document how to create own Python tasks

## Quick start

Create a file `my_playbook.py`:

```python
from anbric.ansible.modules import command
from anbric.core import play
from anbric.modules.file import write_file, copy


@play(hosts='all')
def test_play(host):
    command('hostname')
    write_file('test.txt', 'Hello world!', mode=0o640)
    command('ls -l')
    command('cat test.txt')
```

and `settings.py`:

```python
from anbric.api import Host, SSHConnection

HOSTS = {
    'test1': Host(SSHConnection(hostname='127.0.1.1')),
}
```

Run the playbook with:

    anbric-play my_playbook

Example output:

    $ anbric-play my_playbook
    [18:21:53] PLAY my_playbook.test_play
               Hosts: all
               Hosts list: ['test1']
               Running at host test1
    [18:21:54] TASK command [test1]: changed
               TASK write_file [test1]: ok
               TASK command [test1]: changed
               TASK command [test1]: changed
