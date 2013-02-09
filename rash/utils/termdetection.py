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


import os


def subdict_by_key_prefix(dct, prefix):
    items = []
    for (k, v) in dct.items():
        if k.startswith(prefix):
            items.append((k, v))
    return dict(items)


def detect_terminal(_environ=os.environ):
    """
    Detect "terminal" you are using.

    First, this function checks if you are in tmux, byobu, or screen.
    If not it uses $COLORTERM [#]_ if defined and fallbacks to $TERM.

    .. [#] So, if you are in Gnome Terminal you have "gnome-terminal"
       instead of "xterm-color"".

    """
    if _environ.get('TMUX'):
        return 'tmux'
    elif subdict_by_key_prefix(_environ, 'BYOBU'):
        return 'byobu'
    elif _environ.get('TERM').startswith('screen'):
        return _environ['TERM']
    elif _environ.get('COLORTERM'):
        return _environ['COLORTERM']
    else:
        return _environ.get('TERM')


if __name__ == '__main__':
    print(detect_terminal())
