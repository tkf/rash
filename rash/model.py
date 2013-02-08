class CommandRecord(object):

    """
    Command record.

    >>> CommandRecord()
    <CommandRecord: None(?.?)>
    >>> CommandRecord(
    ... command='DUMMY-COMMAND',
    ... command_history_id=222,
    ... session_history_id=111)
    <CommandRecord: DUMMY-COMMAND(111.222)>

    """

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

    def __repr__(self):
        ch_id = self.command_history_id
        sh_id = self.session_history_id
        return '<{0}: {1}({2}.{3})>'.format(
            self.__class__.__name__,
            self.command,
            sh_id if sh_id is not None else '?',
            ch_id if ch_id is not None else '?',
        )


class SessionRecord(object):

    """
    Session record.

    >>> SessionRecord()
    <SessionRecord: ?>
    >>> SessionRecord(command='DUMMY-COMMAND', session_history_id=111)
    <SessionRecord: 111>

    """

    def __init__(self, **kwds):
        self.session_history_id = None
        self.session_id = None
        self.start = None
        self.stop = None
        self.environ = {}
        self.__dict__.update(kwds)

    def __repr__(self):
        sh_id = self.session_history_id
        return '<{0}: {1}>'.format(
            self.__class__.__name__,
            sh_id if sh_id is not None else '?',
        )


class VersionRecord(object):

    """
    Version record.

    >>> VersionRecord(rash_version='0.2.0', schema_version='0.1')
    <VersionRecord: schema=0.1, rash=0.2.0>

    """

    def __init__(self, **kwds):
        self.id = None
        self.rash_version = None
        self.schema_version = None
        self.updated = None
        self.__dict__.update(kwds)

    def __repr__(self):
        return '<{0}: schema={1}, rash={2}>'.format(
            self.__class__.__name__,
            self.schema_version,
            self.rash_version,
        )
