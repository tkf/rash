def show_run(command_history_id):
    """
    Show detailed command history by its ID.
    """
    from pprint import pprint
    from .config import ConfigStore
    from .database import DataBase
    db = DataBase(ConfigStore().db_path)
    with db.connection():
        for ch_id in command_history_id:
            crec = db.get_full_command_record(ch_id)
            pprint(crec.__dict__)
            print("")


def show_add_arguments(parser):
    parser.add_argument(
        'command_history_id', nargs='+', type=int,
        help="""
        Integer ID of command history.
        """)


commands = [
    ('show', show_add_arguments, show_run),
]
