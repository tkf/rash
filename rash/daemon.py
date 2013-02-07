import os


def daemon_run(no_error, restart, record_path, keep_json, check_duplicate,
               log_level):
    """
    Run RASH index daemon.

    This daemon watches the directory ``~/.config/rash/data/record``
    and translate the JSON files dumped by ``record`` command into
    sqlite3 DB at ``~/.config/rash/data/db.sqlite``.

    ``rash init`` will start RASH automatically by default.
    But there are alternative ways to start daemon.

    If you want to organize background process in one place such
    as supervisord_, it is good to add `--restart` option to force
    stop other daemon process if you accidentally started it in
    other place.  Here is an example of supervisord_ setup::

      [program:rash-daemon]
      command=rash daemon --restart

    .. _supervisord: http://supervisord.org/

    Alternatively, you can call ``rash index`` in cron job to
    avoid using daemon.::

      # Refresh RASH DB every 10 minutes
      */10 * * * * rash index

    """
    # Probably it makes sense to use this daemon to provide search
    # API, so that this daemon is going to be the only process that
    # is connected to the DB?
    from .config import ConfigStore
    from .indexer import Indexer
    from .log import setup_daemon_log_file
    from .watchrecord import watch_record, install_sigterm_handler

    install_sigterm_handler()
    conf = ConfigStore()
    if log_level:
        conf.daemon_log_level = log_level

    # SOMEDAY: make PID checking/writing atomic if possible
    if os.path.exists(conf.daemon_pid_path):
        if no_error:
            return
        with open(conf.daemon_pid_path, 'rt') as f:
            pid = int(f.read().strip())
        if restart:
            stop_running_daemon(conf, pid)
        else:
            raise RuntimeError(
                'There is already a running daemon (PID={0})!'.format(pid))

    with open(conf.daemon_pid_path, 'w') as f:
        f.write(str(os.getpid()))

    try:
        setup_daemon_log_file(conf)
        indexer = Indexer(conf, check_duplicate, keep_json, record_path)
        indexer.index_all()
        watch_record(indexer)
    finally:
        os.remove(conf.daemon_pid_path)


def stop_running_daemon(conf, pid):
    import time
    import signal
    os.kill(pid, signal.SIGTERM)
    for _ in range(30):
        time.sleep(0.1)
        if not os.path.exists(conf.daemon_pid_path):
            break
    else:
        raise RuntimeError(
            'Failed to stop running daemon process (PID={0})'
            .format(pid))


def start_daemon_in_subprocess(options, outpath=os.devnull):
    """
    Run `rash daemon --no-error` in background.

    :type options: list of str
    :arg  options: options for "rash daemon" command
    :type outpath: str
    :arg  outpath: path to redirect daemon output

    """
    import subprocess
    import sys
    from .utils.py3compat import nested
    from .utils.pathutils import mkdirp
    if outpath != os.devnull:
        mkdirp(os.path.dirname(outpath))
    with nested(open(os.devnull),
                open(outpath, 'w')) as (stdin, stdout):
        subprocess.Popen(
            [os.path.abspath(sys.executable), '-m', 'rash.cli',
             'daemon', '--no-error'] + options,
            preexec_fn=os.setsid,
            stdin=stdin, stdout=stdout, stderr=subprocess.STDOUT)


def daemon_add_arguments(parser):
    parser.add_argument(
        '--no-error', action='store_true', default=False,
        help="""
        Do nothing if a daemon is already running.
        """)
    parser.add_argument(
        '--restart', action='store_true', default=False,
        help="""
        Kill already running daemon process if exist.
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
