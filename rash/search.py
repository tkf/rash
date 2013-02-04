def search_run(**kwds):
    """
    [UNDER CONSTRUCTION]
    Search command history.

    """
    from .config import ConfigStore
    from .database import DataBase
    db = DataBase(ConfigStore().db_path)
    for crec in db.search_command_record(**kwds):
        print(crec.command)


def search_add_arguments(parser):
    # Filter
    parser.add_argument(
        'pattern', nargs='*',
        help='glob patterns that matches to command.')
    parser.add_argument(
        '--limit', type=int, default=10,
        help='maximum number of history to show. -1 means not limit.')
    parser.add_argument(
        '--no-unique', dest='unique', action='store_false', default=True,
        help="""
        Include all duplicates.
        """)
    parser.add_argument(
        '--cwd', action='append', default=[],
        help="""
        The working directory at the time when the command was run.
        When given several times, items that match to one of the
        directory are included in the result.
        """)
    parser.add_argument(
        '--cwd-glob', action='append', default=[],
        help="""
        Same as --cwd but it accepts glob expression.
        """)
    parser.add_argument(
        '--time-after',
        help='commands run after the given time')
    parser.add_argument(
        '--time-before',
        help='commands run before the given time')
    parser.add_argument(
        '--duration-longer-than',
        help='commands that takes longer than the given time')
    parser.add_argument(
        '--duration-less-than',
        help='commands that takes less than the given time')
    parser.add_argument(
        '--include-exit-code', action='append', default=[],
        help='include command which finished with given exit code.')
    parser.add_argument(
        '--exclude-exit-code', action='append', default=[],
        help='exclude command which finished with given exit code.')
    # Sorter
    parser.add_argument(
        '--sort-program-frequency',
        help='most used program comes first')
    # Modifier
    parser.add_argument(
        '--after-context', type=int, metavar='NUM',
        help="""
        Print NUM commands executed after matching commands.
        """)
    parser.add_argument(
        '--before-context', type=int, metavar='NUM',
        help="""
        Print NUM commands executed before matching commands.
        """)
    parser.add_argument(
        '--context', type=int, metavar='NUM',
        help="""
        Print NUM commands executed before and after matching commands.
        """)


commands = [
    ('search', search_add_arguments, search_run),
]
