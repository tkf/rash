def server_run():
    """
    [UNDER CONSTRUCTION]
    Run RASH index server.

    This server watches the directory ``~/.config/rash/data/record``
    and translate the JSON files dumped by ``record`` command into
    sqlite3 DB at ``~/.config/rash/data/db.sqlite``.

    """
    # Probably it makes sense to use this server to provide search
    # API, so that this server is going to be the only process that
    # is connected to the DB?
    raise NotImplementedError


def server_add_arguments(parser):
    pass


commands = [
    ('server', server_add_arguments, server_run),
]
