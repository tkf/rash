import os
import sys
PY3 = (sys.version_info[0] >= 3)

try:
    getcwd = os.getcwd
except AttributeError:
    getcwd = os.getcwdu


try:
    from contextlib import nested
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def nested(*managers):
        if managers:
            with managers[0] as ctx:
                with nested(*managers[1:]) as rest:
                    yield (ctx,) + rest
        else:
            yield ()
