"""
Record shell history.

This is a command to be called from shell-specific hooks.
This Python implementation is a reference implementation.
Probably it makes sense to write this command naively in
shells to make it faster.

The dumbed data goes under the ``~/.config/rash/data/dumb``
directory.

"""

import os
import time
import json

from .config import ConfigStore


def dump_run(**kwds):
    """
    Record shell history.
    """
    conf = ConfigStore()
    json_path = os.path.join(conf.dump_path,
                             time.strftime('%Y-%m-%d-%H%M%S.json'))
    data = dict((k, v) for (k, v) in kwds.items() if v is not None)
    data.update(
        shell=os.environ.get('SHELL'),
        term=os.environ.get('TERM'),
        path=os.environ.get('PATH'),
        cwd=os.getcwdu(),
    )
    data.setdefault('stop', int(time.time()))
    with open(json_path, 'w') as fp:
        json.dump(data, fp)


def dump_add_arguments(parser):
    parser.add_argument(
        'command',
        help="command that was ran.")
    parser.add_argument(
        '--exit-code', type=int,
        help="exit code $? of the command.")
    parser.add_argument(
        '--pipestatus', type=int, nargs='+',
        help="$pipestatus (zsh) / $PIPESTATUS (bash)")
    parser.add_argument(
        '--start', type=int,
        help='the time COMMAND is started.')
    parser.add_argument(
        '--stop', type=int,
        help='the time COMMAND is finished.')
    parser.add_argument(
        '--program',
        help='like $TERM, but can be anything (e.g., emacs / tmux).')


commands = [
    ('dump', dump_add_arguments, dump_run),
]
