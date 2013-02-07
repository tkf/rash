class CommandRecord(object):

    def __init__(self, **kwds):
        self.command_history_id = None
        self.command = None
        self.session_history_id = None
        self.session_id = None
        self.exit_code = None
        self.pipestatus = []
        self.start = None
        self.stop = None
        self.terminal = None
        self.cwd = None
        self.environ = {}

        # Non-record attributes (metadata):
        self.command_count = None

        self.__dict__.update(kwds)


class SessionRecord(object):

    def __init__(self, **kwds):
        self.session_history_id = None
        self.session_id = None
        self.start = None
        self.stop = None
        self.environ = {}
        self.__dict__.update(kwds)


class VersionRecord(object):

    def __init__(self, **kwds):
        self.id = None
        self.rash_version = None
        self.schema_version = None
        self.updated = None
        self.__dict__.update(kwds)
