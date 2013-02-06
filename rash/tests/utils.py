import unittest
import functools
from contextlib import contextmanager


class BaseTestCase(unittest.TestCase):

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, member, container):
            self.assertTrue(member in container)

    if not hasattr(unittest.TestCase, 'assertNotIn'):
        def assertNotIn(self, member, container):
            self.assertTrue(member not in container)

    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, obj, cls, msg=None):
            self.assertTrue(isinstance(obj, cls), msg)

try:
    skipIf = unittest.skipIf
except AttributeError:

    def skipIf(condition, reason):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwds):
                if condition:
                    print("Skipping {0} because:".format(func.__name__))
                    print(reason)
                else:
                    return func(*args, **kwds)
            return wrapper
        return decorator


@contextmanager
def monkeypatch(obj, name, attr):
    """
    Context manager to replace attribute named `name` in `obj` with `attr`.
    """
    orig = getattr(obj, name)
    setattr(obj, name, attr)
    yield
    setattr(obj, name, orig)
