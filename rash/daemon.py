def daemon_run():
    """
    [UNDER CONSTRUCTION]
    Run RASH index daemon.

    This daemon watches the directory ``~/.config/rash/data/record``
    and translate the JSON files dumped by ``record`` command into
    sqlite3 DB at ``~/.config/rash/data/db.sqlite``.

    """
    # Probably it makes sense to use this daemon to provide search
    # API, so that this daemon is going to be the only process that
    # is connected to the DB?
    raise NotImplementedError


def daemon_add_arguments(parser):
    pass


commands = [
    ('daemon', daemon_add_arguments, daemon_run),
]
