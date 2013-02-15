"""
Record shell history.

This is a command to be called from shell-specific hooks.
This Python implementation is a reference implementation.
Probably it makes sense to write this command naively in
shells to make it faster.

The dumped data goes under the ``~/.config/rash/data/record``
directory.

"""

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
import time
import json

from .utils.pathutils import mkdirp
from .utils.py3compat import getcwd
from .config import ConfigStore


def get_tty():
    """
    Return \"os.ttyname(0 or 1 or 2)\".
    """
    for i in range(3):
        try:
            return os.ttyname(i)
            break
        except OSError:
            pass


def get_environ(keys):
    """
    Get environment variables from :data:`os.environ`.

    :type keys: [str]
    :rtype: dict

    Some additional features.

    * If 'HOST' is not in :data:`os.environ`, this function
      automatically fetch it using :meth:`platform.node`.
    * If 'TTY' is not in :data:`os.environ`, this function
      automatically fetch it using :meth:`os.ttyname`.
    * Set 'RASH_SPENV_TERMINAL' if needed.

    """
    items = ((k, os.environ.get(k)) for k in keys)
    subenv = dict((k, v) for (k, v) in items if v is not None)
    needset = lambda k: k in keys and not subenv.get(k)

    def setifnonempty(key, value):
        if value:
            subenv[key] = value

    if needset('HOST'):
        import platform
        subenv['HOST'] = platform.node()
    if needset('TTY'):
        setifnonempty('TTY', get_tty())
    if needset('RASH_SPENV_TERMINAL'):
        from .utils.termdetection import detect_terminal
        setifnonempty('RASH_SPENV_TERMINAL', detect_terminal())
    return subenv


def generate_session_id(data):
    """
    Generate session ID based on HOST, TTY, PID [#]_ and start time.

    :type data: dict
    :rtype: str

    .. [#] PID of the shell, i.e., PPID of this Python process.

    """
    host = data['environ']['HOST']
    tty = data['environ'].get('TTY') or 'NO_TTY'
    return ':'.join(map(str, [
        host, tty, os.getppid(), data['start']]))


def record_run(record_type, print_session_id, **kwds):
    """
    Record shell history.
    """
    if print_session_id and record_type != 'init':
        raise RuntimeError(
            '--print-session-id should be used with --record-type=init')

    cfstore = ConfigStore()
    # SOMEDAY: Pass a list of environment variables to shell by "rash
    # init" and don't read configuration in "rash record" command.  It
    # is faster.
    config = cfstore.get_config()
    envkeys = config.record.environ[record_type]
    json_path = os.path.join(cfstore.record_path,
                             record_type,
                             time.strftime('%Y-%m-%d-%H%M%S.json'))
    mkdirp(os.path.dirname(json_path))

    # Command line options directly map to record keys
    data = dict((k, v) for (k, v) in kwds.items() if v is not None)
    data.update(
        environ=get_environ(envkeys),
    )

    # Automatically set some missing variables:
    data.setdefault('cwd', getcwd())
    if record_type in ['command', 'exit']:
        data.setdefault('stop', int(time.time()))
    elif record_type in ['init']:
        data.setdefault('start', int(time.time()))

    if print_session_id:
        data['session_id'] = generate_session_id(data)
        print(data['session_id'])

    with open(json_path, 'w') as fp:
        json.dump(data, fp)


def record_add_arguments(parser):
    parser.add_argument(
        '--record-type', default='command',
        choices=['command', 'init', 'exit'],
        help='type of record to store.')
    parser.add_argument(
        '--command',
        help="command that was ran.")
    parser.add_argument(
        '--cwd',
        help='''
        Like $PWD, but callee can set it to consider command that
        changes directory (e.g., cd).
        ''')
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
        '--session-id',
        help='''
        RASH session ID generated by --print-session-id.
        This option should be used with `command` or `exit` RECORD_TYPE.
        ''')
    parser.add_argument(
        '--print-session-id', default=False, action='store_true',
        help='''
        print generated session ID to stdout.
        This option should be used with `init` RECORD_TYPE.
        ''')


commands = [
    ('record', record_add_arguments, record_run),
]
