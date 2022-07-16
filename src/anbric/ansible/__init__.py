import importlib
import json
import sys
import tempfile
import traceback

from ansible_mitogen.runner import NewStyleStdio, TemporaryArgv, TempFileWatcher, AtExitWrapper

from anbric.core import Vars, Result


class NewStyleRunner:
    """
    Taken mostly from ansible_mitogen. It's very probable we can use it directly,
    once I [FS] understand the purpose of module_map and the interaction between services
    in ansible_mitogen. So this is a stripped version that makes the implementation
    understandable without knowing much about ansible_mitogen at the expense of (presumably)
    not being compatible with many Ansible modules.
    """

    def __init__(self, module, args, module_entrypoint='main'):
        self.module_entrypoint = module_entrypoint
        self._temp_dir = None
        self.args = args
        self.atexit_wrapper = None
        self._temp_watcher = None
        self._argv = None
        self._stdio = None
        self.module = module

    def _revert_excepthook(self):
        sys.excepthook = self.original_excepthook

    def __enter__(self):
        self._stdio = NewStyleStdio(self.args, self.get_temp_dir())
        # It is possible that not supplying the script filename will break some
        # module, but this has never been a bug report. Instead act like an
        # interpreter that had its script piped on stdin.
        self._argv = TemporaryArgv([''])
        self._temp_watcher = TempFileWatcher()
        self._setup_excepthook()
        self.atexit_wrapper = AtExitWrapper()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.atexit_wrapper.revert()
        self._temp_watcher.revert()
        self._argv.revert()
        self._stdio.revert()
        self._revert_excepthook()

    def _setup_excepthook(self):
        """
        Starting with Ansible 2.6, some modules (file.py) install a
        sys.excepthook and never clean it up. So we must preserve the original
        excepthook and restore it after the run completes.
        """
        self.original_excepthook = sys.excepthook

    def run(self):
        mod = importlib.import_module(self.module)

        rc = 2
        try:
            try:
                getattr(mod, self.module_entrypoint)()
            except SystemExit:
                exc = sys.exc_info()[1]
                rc = exc.args[0]
            except Exception:
                # This writes to stderr by default.
                traceback.print_exc()
                rc = 1

        finally:
            self.atexit_wrapper.run_callbacks()

        return {
            'rc': rc,
            'stdout': sys.stdout.getvalue(),
            'stderr': sys.stderr.getvalue(),
        }

    def get_temp_dir(self):
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix='fabfab_')

        return self._temp_dir


def _execute(module_name, args):
    with NewStyleRunner(module_name, args=args) as r:
        return r.run()


def ansible_module(module_name, params):
    received = Vars.context.call(_execute, module_name, params)

    stdout = json.loads(received['stdout'])
    res = Result(rc=received['rc'], changed=stdout['changed'], res=stdout,
                 stdout=received['stdout'], stderr=received['stderr'])
    return res
