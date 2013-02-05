import unittest

from ..termdetection import detect_terminal


class TestTerminalDetection(unittest.TestCase):

    def assert_terminal(self, terminal, environ):
        self.assertEqual(detect_terminal(_environ=environ), terminal)

    def test_tmux(self):
        self.assert_terminal(
            'tmux',
            {'TMUX': 'some value', 'TERM': 'screen'})

    def test_byobu(self):
        self.assert_terminal(
            'byobu',
            {'BYOBU_WINDOWS': 'some/path', 'TERM': 'screen'})

    def test_screen(self):
        self.assert_terminal(
            'screen',
            {'TERM': 'screen', 'COLORTERM': 'gnome-terminal'})

    def test_gnome_terminal(self):
        self.assert_terminal(
            'gnome-terminal',
            {'COLORTERM': 'gnome-terminal', 'TERM': 'xterm-color'})

    def test_fallback(self):
        self.assert_terminal('xterm', {'TERM': 'xterm'})
