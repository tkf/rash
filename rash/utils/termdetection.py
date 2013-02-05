import os


def subdict_by_key_prefix(dct, prefix):
    items = []
    for (k, v) in dct.iteritems():
        if k.startswith(prefix):
            items.append((k, v))
    return dict(items)


def detect_terminal():
    """
    Detect "terminal" you are using.

    First, this function checks if you are in tmux, byobu, or screen.
    If not it uses $COLORTERM [#]_ if defined and fallbacks to $TERM.

    .. [#] So, if you are in Gnome Terminal you have "gnome-terminal"
       instead of "xterm-color"".

    """
    if os.environ.get('TMUX'):
        return 'tmux'
    elif subdict_by_key_prefix(os.environ, 'BYOBU'):
        return 'byobu'
    elif os.environ.get('TERM').startswith('screen'):
        return os.environ['TERM']
    elif os.environ.get('COLORTERM'):
        return os.environ['COLORTERM']
    else:
        return os.environ.get('TERM')


if __name__ == '__main__':
    print(detect_terminal())
