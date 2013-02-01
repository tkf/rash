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
