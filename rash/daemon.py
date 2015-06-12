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


import os


def daemon_run(no_error, restart, record_path, keep_json, check_duplicate,
               use_polling, log_level):
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
    avoid using daemon.  It is useful if you want to use RASH
    on NFS, as it looks like watchdog does not work on NFS.::

      # Refresh RASH DB every 10 minutes
      */10 * * * * rash index

    """
    # Probably it makes sense to use this daemon to provide search
    # API, so that this daemon is going to be the only process that
    # is connected to the DB?
    from .config import ConfigStore
    from .indexer import Indexer
    from .log import setup_daemon_log_file, LogForTheFuture
    from .watchrecord import watch_record, install_sigterm_handler

    install_sigterm_handler()
    cfstore = ConfigStore()
    if log_level:
        cfstore.daemon_log_level = log_level
    flogger = LogForTheFuture()

    # SOMEDAY: make PID checking/writing atomic if possible
    flogger.debug('Checking old PID file %r.', cfstore.daemon_pid_path)
    if os.path.exists(cfstore.daemon_pid_path):
        flogger.debug('Old PID file exists.  Reading from it.')
        with open(cfstore.daemon_pid_path, 'rt') as f:
            pid = int(f.read().strip())
        flogger.debug('Checking if old process with PID=%d is alive', pid)
        try:
            os.kill(pid, 0)     # check if `pid` is alive
        except OSError:
            flogger.info(
                'Process with PID=%d is already dead.  '
                'So just go on and use this daemon.', pid)
        else:
            if restart:
                flogger.info('Stopping old daemon with PID=%d.', pid)
                stop_running_daemon(cfstore, pid)
            else:
                message = ('There is already a running daemon (PID={0})!'
                           .format(pid))
                if no_error:
                    flogger.debug(message)
                    # FIXME: Setup log handler and flogger.dump().
                    # Note that using the default log file is not safe
                    # since it has already been used.
                    return
                else:
                    raise RuntimeError(message)
    else:
        flogger.debug('Daemon PID file %r does not exists.  '
                      'So just go on and use this daemon.',
                      cfstore.daemon_pid_path)

    with open(cfstore.daemon_pid_path, 'w') as f:
        f.write(str(os.getpid()))

    try:
        setup_daemon_log_file(cfstore)
        flogger.dump()
        indexer = Indexer(cfstore, check_duplicate, keep_json, record_path)
        indexer.index_all()
        watch_record(indexer, use_polling)
    finally:
        os.remove(cfstore.daemon_pid_path)


def stop_running_daemon(cfstore, pid):
    import time
    import signal
    os.kill(pid, signal.SIGTERM)
    for _ in range(30):
        time.sleep(0.1)
        if not os.path.exists(cfstore.daemon_pid_path):
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
        '--use-polling', default=False, action='store_true',
        help="""
        Use polling instead of system specific notification.
        This is useful, for example, when your $HOME is on NFS where
        inotify does not work.
        """)
    parser.add_argument(
        '--log-level',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        help='logging level.')


commands = [
    ('daemon', daemon_add_arguments, daemon_run),
]
