class CommandRecord(object):

    def __init__(self, **kwds):
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
        self.__dict__.update(kwds)


class SessionRecord(object):

    def __init__(self, **kwds):
        self.session_history_id = None
        self.session_id = None
        self.start = None
        self.stop = None
        self.environ = {}
        self.__dict__.update(kwds)
