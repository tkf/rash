import os


def shell_name(shell):
    return shell.rsplit(os.path.sep, 1)[-1]


def find_init(shell):
    rash_dir = os.path.dirname(__file__)
    return os.path.join(rash_dir, 'ext', 'rash.{0}'.format(shell_name(shell)))


def init_run(shell, no_daemon):
    """
    Configure your shell.

    Add the following line in your shell RC file and then you are
    ready to go::

      source $(%(prog)s)

    To check if your shell is supported, simply run::

      %(prog)s

    By default, this command also starts daemon in background to
    automatically inndex shell history records.  To not start daemon,
    use --no-daemon option.

    Following shell variables can be set to control initialize
    sequence for your shell.

    RASH_INIT_NO_DAEMON : "t" | ""
      Set ths to "t" to not start "rash daemon" on init.

    RASH_INIT_DAEMON_OPTIONS : space separated options
      Options passed to "rash daemon" command.
      Note that --no-error is always passed to the command.

    RASH_INIT_DAEMON_OUT : file path
      Dump STDOUT/STDERR of "rash daemon" process to here.
      Default is /dev/null.

    **Example**::

      RASH_INIT_NO_DAEMON=t  # Do not start "rash daemon" on init.
      source $(%(prog)s)

    """
    init_file = find_init(shell)
    if os.path.exists(init_file):
        print(init_file)
    else:
        raise RuntimeError(
            "Shell '{0}' is not supported.".format(shell_name(shell)))

    if not no_daemon:
        from .daemon import start_daemon_in_subprocess
        # FIXME: Make options to be passed to daemon command optional.
        start_daemon_in_subprocess(['--keep-json', '--log-level=DEBUG'])


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


commands = [
    ('init', init_add_arguments, init_run),
]
