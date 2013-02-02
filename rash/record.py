"""
Record shell history.

This is a command to be called from shell-specific hooks.
This Python implementation is a reference implementation.
Probably it makes sense to write this command naively in
shells to make it faster.

The dumped data goes under the ``~/.config/rash/data/record``
directory.

"""

import os
import time
import json

from .utils.pathutils import mkdirp
from .config import ConfigStore


def get_environ(*keys):
    items = ((k, os.environ.get(k)) for k in keys)
    return dict((k, v) for (k, v) in items if v is not None)


def record_run(**kwds):
    """
    Record shell history.
    """
    conf = ConfigStore()
    json_path = os.path.join(conf.record_path,
                             'command',
                             time.strftime('%Y-%m-%d'),
                             time.strftime('%H%M%S.json'))
    mkdirp(os.path.dirname(json_path))
    data = dict((k, v) for (k, v) in kwds.items() if v is not None)
    data.update(
        environ=get_environ('SHELL', 'TERM', 'PATH'),
        cwd=os.getcwdu(),
    )
    data.setdefault('stop', int(time.time()))
    with open(json_path, 'w') as fp:
        json.dump(data, fp)


def record_add_arguments(parser):
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
        '--terminal',
        help='like $TERM, but can be anything (e.g., emacs / tmux).')


commands = [
    ('record', record_add_arguments, record_run),
]
