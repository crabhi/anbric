import difflib
import io
import json
import os.path
import tempfile
import traceback
from typing import Union

from ansible_mitogen.target import transfer_file

from anbric.core import VARS, Result, task


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

    if dirname and makedirs:
        os.makedirs(dirname, exist_ok=True)

    if isinstance(content, str):
        content = content.encode(encoding)

    changed = False

    if not os.path.exists(dest):
        existing = []
        existing_mode = None
    else:
        with open(dest, 'rb') as df:
            stat = os.fstat(df.fileno())
            existing_mode = stat.st_mode & 0o777
            existing = df.readlines()

    new_lines = content.splitlines(keepends=True)
    diff = b''.join(difflib.diff_bytes(difflib.unified_diff, existing, new_lines,
                                         f'master:{src_path}'.encode('utf-8'),
                                         f'{os.path.abspath(dest)}'.encode('utf-8'))).decode('utf-8', errors='replace')
    if new_lines != existing:
        changed = True
        tmpdest_fd, tmpdest = tempfile.mkstemp(dir=dirname, prefix='.transfer_')
        try:
            f = os.fdopen(tmpdest_fd, 'wb')
            try:
                f.write(content)
            finally:
                f.close()
            if mode:
                os.chmod(tmpdest, mode)
            os.rename(tmpdest, dest)
        except Exception:
            os.unlink(tmpdest)
            os.close(tmpdest_fd)
            return {
                "rc": 1,
                "stderr": traceback.format_stack(),
                "stdout": "",
            }
    elif mode and existing_mode != mode:
        changed = True
        os.chmod(dest, mode)

    ret = {
        "diff": diff,
        "changed": changed,
        "msg": dest,
    }

    return {
        "rc": 0,
        "stdout": json.dumps(ret),
        "stderr": "",
    }


def copy(dest: str, src=None, content=None, name="copy"):
    if (src is None) == (content is None):
        raise ValueError('You must set either src or content, not both')

    if src and VARS.context.call(os.path.isdir, dest):
        dest = os.path.join(dest, os.path.basename(src))

    if content is None:
        with open(src, 'rb') as f:
            content = f.read()

    return write_file(dest, content, src_path=src, name=name)
