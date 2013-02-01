def index_run():
    """
    [UNDER CONSTRUCTION]
    Convert raw JSON records into sqlite3 DB.

    .. note:: The idea is to use this command at early stage of
       development with --keep-json, so that there is no need for
       DB migration when schema is updated.

    """
    raise NotImplementedError


def index_add_arguments(parser):
    parser.add_argument(
        'record_directory', nargs='?',
        help="""
        specify the directory that has JSON records.
        """)
    parser.add_argument(
        '--keep-json',
        help="""
        Do not remove old JSON files.  It turns on --check-duplicate.
        """)
    parser.add_argument(
        '--check-duplicate', default=False, action='store_true',
        help='do not store already existing history in DB.')


commands = [
    ('index', index_add_arguments, index_run),
]
