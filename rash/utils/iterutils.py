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


import itertools


def nonempty(iterative):
    """
    True if `iterative` returns at least one element.

    >>> nonempty(iter([1]))
    True
    >>> nonempty(iter([]))
    False

    """
    for _ in iterative:
        return True
    return False


def repeat(item, num):
    return itertools.islice(itertools.repeat(item), num)
