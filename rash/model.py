class CommandRecord(object):

    def __init__(self, **kwds):
        self.command = None
        self.exit_code = None
        self.pipestatus = []
        self.start = None
        self.stop = None
        self.terminal = None
        self.cwd = None
        self.environ = {}
        self.__dict__.update(kwds)
