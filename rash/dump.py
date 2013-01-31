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


def dump_add_arguments(parser):
    parser.add_argument(
        'command',
        help="command that was ran.")


def dump_run(*kwds):
    """
    Record shell history.
    """
    conf = ConfigStore()
    json_path = os.path.join(conf.dump_path,
                             time.strftime('%Y-%m-%d-%H%M%S.json'))
    data = kwds
    data.update(
        time=int(time.time()),
        shell=os.environ.get('SHELL'),
        cwd=os.getcwdu(),
    )
    with open(json_path, 'w') as fp:
        json.dump(data, fp)


commands = [
    ('dump', dump_add_arguments, dump_run),
]
