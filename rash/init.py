import os


def shell_name(shell):
    return shell.rsplit(os.path.sep, 1)[-1]


def find_init(shell):
    rash_dir = os.path.dirname(__file__)
    return os.path.join(rash_dir, 'ext', 'rash.{0}'.format(shell_name(shell)))


def init_run(shell, no_daemon):
    """
    Show path to a file to configure shell.

    Usage::

      source $(%(prog)s)

    """
    init_file = find_init(shell)
    if os.path.exists(init_file):
        print(init_file)
    else:
        raise RuntimeError(
            "Shell '{0}' is not supported.".format(shell_name(shell)))

    # FIXME: Use the following once daemon is implemented.
    if False:  # not no_daemon:
        from .daemon import start_daemon_in_subprocess
        start_daemon_in_subprocess()


def init_add_arguments(parser):
    parser.add_argument(
        '--shell', default=os.environ.get('SHELL'),
        help="""
        name of shell you are using.  directory before the last /
        is discarded.
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
