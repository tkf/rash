import unittest
import functools


class BaseTestCase(unittest.TestCase):

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, member, container):
            self.assertTrue(member in container)

    if not hasattr(unittest.TestCase, 'assertNotIn'):
        def assertNotIn(self, member, container):
            self.assertTrue(member not in container)

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
