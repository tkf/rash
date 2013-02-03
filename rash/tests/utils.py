import unittest


class BaseTestCase(unittest.TestCase):

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, member, container):
            self.assertTrue(member in container)
