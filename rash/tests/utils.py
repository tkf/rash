import unittest


class BaseTestCase(unittest.TestCase):

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, member, container):
            self.assertTrue(member in container)

    if not hasattr(unittest.TestCase, 'assertNotIn'):
        def assertNotIn(self, member, container):
            self.assertTrue(member not in container)
