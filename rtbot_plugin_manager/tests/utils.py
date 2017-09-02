# from https://gist.github.com/japsu/1931430#file-mkxtemp-py-L11

import os
import sys
import tempfile
from contextlib import contextmanager


@contextmanager
def OpenableNamedTemporaryFile(*args, content, **kwargs):
    with tempfile.NamedTemporaryFile(*args, delete=False, **kwargs) as f:
        f.write(content)
    try:
        yield f.name
    finally:
        os.unlink(f.name)


@contextmanager
def SysPath(path):
    sys.path.insert(0, path)
    yield
    sys.path.remove(path)
