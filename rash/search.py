def search_run(pattern):
    """
    [UNDER CONSTRUCTION]
    Search command history.

    """
    raise NotImplementedError


def search_add_arguments(parser):
    # Filter
    parser.add_argument(
        'pattern', nargs='*',
        help='glob patterns that matches to command.')
    parser.add_argument(
        '--cwd', action='append', default=[],
        help="""
        The working directory at the time when the command was run.
        It accepts glob expression.  When given several times, items
        that match to one of the directory are included in the result.
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


commands = [
    ('search', search_add_arguments, search_run),
]
