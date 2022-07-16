import difflib
import io
import json
import os.path
import tempfile
import traceback
from typing import Union

from ansible_mitogen.target import transfer_file

from anbric.core import Vars, Result, task


@task
def write_file(
        dest: str,
        content: Union[bytes, str],
        encoding='utf-8',
        src_path: str = None,
        makedirs=True,
        mode: int = None,
):
    dirname = os.path.dirname(dest)

    if makedirs:
        os.makedirs(dirname, exist_ok=True)

    if isinstance(content, str):
        content = content.encode(encoding, errors='replace')

    if not os.path.exists(dest):
        existing = []
    else:
        with open(dest, 'r', encoding=encoding) as df:
            existing = df.readlines()

    new_lines = content.splitlines(keepends=True)
    changed = new_lines != existing

    diff = list(difflib.diff_bytes(difflib.unified_diff, existing, new_lines,
                                   f'master:{src_path}'.encode('utf-8'),
                                   f'{dest}'.encode('utf-8')))

    tmpdest_fd, tmpdest = tempfile.mkstemp(dir=dirname, prefix='.transfer_')
    try:
        f = os.fdopen(tmpdest_fd, 'wb')
        try:
            f.write(content)
        finally:
            f.close()
        os.rename(tmpdest, dest)
    except Exception:
        os.unlink(tmpdest)
        os.close(tmpdest_fd)
        return {
            "rc": 1,
            "stderr": traceback.format_stack(),
            "stdout": "",
        }

    ret = {
        "diff": diff,
        "changed": changed,
        "msg": dest,
    }

    return {
        "rc": 0,
        "stdout": json.dumps(ret)
    }


def copy(dest: str, src=None, content=None, name="copy"):
    if (src is None) == (content is None):
        raise ValueError('You must set either src or content, not both')

    if content is None:
        with open(src, 'rb') as f:
            content = f.read()
            write_file(dest, content)

    return Result(task_name=name, rc=0,
                 changed=True, msg=dest, stdout="", stderr="")
