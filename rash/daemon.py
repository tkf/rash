import os
import sys
import subprocess


def daemon_run():
    """
    [UNDER CONSTRUCTION]
    Run RASH index daemon.

    This daemon watches the directory ``~/.config/rash/data/record``
    and translate the JSON files dumped by ``record`` command into
    sqlite3 DB at ``~/.config/rash/data/db.sqlite``.

    """
    # Probably it makes sense to use this daemon to provide search
    # API, so that this daemon is going to be the only process that
    # is connected to the DB?
    raise NotImplementedError


def start_daemon_in_subprocess():
    """
    Run `rash daemon --no-error` in background.
    """
    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(
            [os.path.abspath(sys.executable), '-m', 'rash.cli',
             'daemon', '--no-error'],
            stdin=devnull, stdout=devnull, stderr=devnull)


def daemon_add_arguments(parser):
    parser.add_argument(
        '--no-error', action='store_true', default=False,
        help="""
        Do nothing if a daemon is already running.
        """)


commands = [
    ('daemon', daemon_add_arguments, daemon_run),
]
