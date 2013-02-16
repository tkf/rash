# Copyright (C) 2013-  Takafumi Arakaki

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import unittest
import functools
from contextlib import contextmanager

from ..utils.py3compat import zip_longest


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

    if not hasattr(unittest.TestCase, 'assertSetEqual'):
        def assertSetEqual(self, set1, set2, msg=None):
            self.assertEqual(set1, set2, msg)

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


def zip_dict(dictionary, fillvalue=None):
    """
    Zip values in `dictionary` and yield dictionaries with same keys.

    >>> list(zip_dict({'a': [1, 2, 3], 'b': [4, 5]}))
    [{'a': 1, 'b': 4}, {'a': 2, 'b': 5}, {'a': 3, 'b': None}]

    """
    (keys, lists) = zip(*dictionary.items())
    for values in zip_longest(*lists, fillvalue=fillvalue):
        yield dict(zip(keys, values))
