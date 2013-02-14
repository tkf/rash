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


def shell_name(shell):
    return shell.rsplit(os.path.sep, 1)[-1]


def find_init(shell):
    rash_dir = os.path.dirname(__file__)
    return os.path.join(rash_dir, 'ext', 'rash.{0}'.format(shell_name(shell)))


INIT_TEMPLATE = """\
source '{file}'
_RASH_VERSION='{version}'
"""
# Currently `_RASH_VERSION` is not used anywhere, but it is useful to
# see when RASH for a long lasting shell session is initialized.


def init_run(shell, no_daemon, daemon_options, daemon_outfile):
    """
    Configure your shell.

    Add the following line in your shell RC file and then you are
    ready to go::

      eval $(%(prog)s)

    To check if your shell is supported, simply run::

      %(prog)s --no-daemon

    If you want to specify shell other than $SHELL, you can give
    --shell option::

      eval $(%(prog)s --shell zsh)

    By default, this command also starts daemon in background to
    automatically index shell history records.  To not start daemon,
    use --no-daemon option like this::

      eval $(%(prog)s --no-daemon)

    To see the other methods to launch the daemon process, see
    ``rash daemon --help``.

    """
    import sys
    from .__init__ import __version__
    init_file = find_init(shell)
    if os.path.exists(init_file):
        sys.stdout.write(INIT_TEMPLATE.format(
            file=init_file, version=__version__))
    else:
        raise RuntimeError(
            "Shell '{0}' is not supported.".format(shell_name(shell)))

    if not no_daemon:
        from .daemon import start_daemon_in_subprocess
        start_daemon_in_subprocess(daemon_options, daemon_outfile)


def init_add_arguments(parser):
    parser.add_argument(
        '--shell', default=os.environ.get('SHELL'),
        help="""
        name of shell you are using.  directory before the last /
        is discarded.  It defaults to $SHELL.
        """)
    parser.add_argument(
        '--no-daemon', action='store_true', default=False,
        help="""
        Do not start daemon.  By default, daemon is started if
        there is no already running daemon.
        """)
    parser.add_argument(
        '--daemon-opt', dest='daemon_options', action='append', default=[],
        help="""
        Add options given to daemon.  See "rash daemon --help" for
        available options.  It can be specified many times.
        Note that --no-error is always passed to the daemon command.
        """)
    parser.add_argument(
        '--daemon-outfile', default=os.devnull,
        help="""
        Path to redirect STDOUT and STDERR of daemon process.
        This is mostly for debugging.
        """)


commands = [
    ('init', init_add_arguments, init_run),
]
