def index_run(record_path, keep_json, check_duplicate):
    """
    [UNDER CONSTRUCTION]
    Convert raw JSON records into sqlite3 DB.

    .. note:: The idea is to use this command at early stage of
       development with --keep-json, so that there is no need for
       DB migration when schema is updated.

    """
    import os
    from .config import ConfigStore
    from .database import DataBase

    if not keep_json:
        raise RuntimeError('At this point, --keep-json should be specified.')

    conf = ConfigStore()
    if keep_json:
        check_duplicate = True
    if not record_path:
        record_path = conf.record_path
    db = DataBase(conf.db_path)

    with db.connection():
        for (root, _, files) in os.walk(record_path):
            for f in (f for f in files if f.endswith('.json')):
                json_path = os.path.join(root, f)
                db.import_json(json_path, check_duplicate=check_duplicate)
                if not keep_json:
                    os.remove(json_path)


def index_add_arguments(parser):
    parser.add_argument(
        'record_path', nargs='?',
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


commands = [
    ('index', index_add_arguments, index_run),
]
