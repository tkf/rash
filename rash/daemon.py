import os
import sys
import subprocess


def daemon_run(no_error, record_path, keep_json, check_duplicate,
               log_level):
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
    from .config import ConfigStore
    from .indexer import Indexer
    from .log import setup_daemon_log_file
    from .watchrecord import watch_record

    conf = ConfigStore()
    if log_level:
        conf.daemon_log_level = log_level

    # FIXME: make PID checking/writing atomic if possible
    if os.path.exists(conf.daemon_pid_path):
        if no_error:
            return
        else:
            pid = open(conf.daemon_pid_path, 'rt').read().strip()
            raise RuntimeError(
                'There is already a running daemon (PID={0})!'.format(pid))
    else:
        with open(conf.daemon_pid_path, 'w') as f:
            f.write(str(os.getpid()))

    try:
        setup_daemon_log_file(conf)
        indexer = Indexer(conf, check_duplicate, keep_json, record_path)
        watch_record(indexer)
    finally:
        os.remove(conf.daemon_pid_path)


def start_daemon_in_subprocess():
    """
    Run `rash daemon --no-error` in background.

    FIXME: This function is not functional.  Its intention is to keep
           the subprocess for daemon alive even after this Python
           process exit.  Current workaround it to use shell to start
           them in background.  See (./ext/rash.zsh, ./ext/rash.bash).

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
    parser.add_argument(
        '--record-path',
        help="""
        specify the directory that has JSON records.
        """)
    parser.add_argument(
        '--keep-json', default=False, action='store_true',
        help="""
        Do not remove old JSON files.  It turns on --check-duplicate.
        """)
    parser.add_argument(
        '--check-duplicate', default=False, action='store_true',
        help='do not store already existing history in DB.')
    parser.add_argument(
        '--log-level',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        help='logging level.')


commands = [
    ('daemon', daemon_add_arguments, daemon_run),
]
