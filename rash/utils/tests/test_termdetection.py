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
