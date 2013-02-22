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

from .py3compat import zip


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


def _backward_shifted_predicate(predicate, num, iterative, include_zero=True):
    queue = []
    for elem in iterative:
        if predicate(elem):
            for q in queue:
                yield True
            yield include_zero
            queue = []
        else:
            queue.append(elem)
            if len(queue) > num:
                queue.pop(0)
                yield False
    for _ in queue:
        yield False


def _forward_shifted_predicate(predicate, num, iterative, include_zero=True):
    counter = 0
    for elem in iterative:
        if predicate(elem):
            counter = num
            yield include_zero
        elif counter > 0:
            yield True
            counter -= 1
        else:
            yield False


def include_before(predicate, num, iterative):
    """
    Return elements in `iterative` including `num`-before elements.

    >>> list(include_before(lambda x: x == 'd', 2, 'abcded'))
    ['b', 'c', 'd', 'e', 'd']

    """
    (it0, it1) = itertools.tee(iterative)
    ps = _backward_shifted_predicate(predicate, num, it1)
    return (e for (e, p) in zip(it0, ps) if p)


def include_after(predicate, num, iterative):
    """
    Return elements in `iterative` including `num`-after elements.

    >>> list(include_after(lambda x: x == 'b', 2, 'abcbcde'))
    ['b', 'c', 'b', 'c', 'd']

    """
    (it0, it1) = itertools.tee(iterative)
    ps = _forward_shifted_predicate(predicate, num, it1)
    return (e for (e, p) in zip(it0, ps) if p)


def include_context(predicate, num, iterative):
    """
    Return elements in `iterative` including `num` before and after elements.

    >>> ''.join(include_context(lambda x: x == '!', 2, 'bb!aa__bb!aa'))
    'bb!aabb!aa'

    """
    (it0, it1, it2) = itertools.tee(iterative, 3)
    psf = _forward_shifted_predicate(predicate, num, it1)
    psb = _backward_shifted_predicate(predicate, num, it2)
    return (e for (e, pf, pb) in zip(it0, psf, psb) if pf or pb)
