SORT_KEY_SYNONYMS = {
    'count': 'command_count',
    'time': 'start_time',
    'start': 'start_time',
    'stop': 'stop_time',
    'code': 'exit_code',
}


def search_run(output, format, with_command_id, with_session_id, **kwds):
    """
    Search command history.

    """
    from .config import ConfigStore
    from .database import DataBase

    if with_command_id and with_session_id:
        format = ("{session_history_id:>5}  "
                  "{command_history_id:>5}  {command}\n")
    elif with_command_id:
        format = "{command_history_id:>5}  {command}\n"
    elif with_session_id:
        format = "{session_history_id:>5}  {command}\n"
    else:
        format = format.decode('string_escape')

    db = DataBase(ConfigStore().db_path)
    for crec in db.search_command_record(**preprocess_kwds(kwds)):
        output.write(format.format(**crec.__dict__))


def preprocess_kwds(kwds):
    """
    Preprocess keyword arguments for `DataBase.search_command_record`.
    """
    from .utils.timeutils import parse_datetime, parse_duration

    for key in ['(output', 'format', 'with_command_id', 'with_session_id']:
        kwds.pop(key, None)

    for key in ['time_after', 'time_before']:
        val = kwds[key]
        if val:
            dt = parse_datetime(val)
            if dt:
                kwds[key] = dt

    for key in ['duration_longer_than', 'duration_less_than']:
        val = kwds[key]
        if val:
            dt = parse_duration(val)
            if dt:
                kwds[key] = dt

    kwds['sort_by'] = SORT_KEY_SYNONYMS[kwds['sort_by']]
    return kwds


def search_add_arguments(parent_parser):
    import argparse
    # Filter
    parser = parent_parser.add_argument_group('Filter')
    parser.add_argument(
        'pattern', nargs='*',
        help='glob patterns that matches to command.')
    parser.add_argument(
        '--exclude-pattern', action='append', default=[],
        help='glob patterns that matches to commands to exclude.')
    parser.add_argument(
        '--limit', type=int, default=10,
        help='maximum number of history to show. -1 means not limit.')
    parser.add_argument(
        '--no-unique', dest='unique', action='store_false', default=True,
        help="""
        Include all duplicates.
        """)
    parser.add_argument(
        '--cwd', action='append', default=[],
        help="""
        The working directory at the time when the command was run.
        When given several times, items that match to one of the
        directory are included in the result.
        """)
    parser.add_argument(
        '--cwd-glob', action='append', default=[],
        help="""
        Same as --cwd but it accepts glob expression.
        """)
    parser.add_argument(
        '--cwd-under', action='append', default=[],
        help="""
        Same as --cwd but include all subdirectories.
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
        '--include-exit-code', action='append', default=[], type=int,
        help='include command which finished with given exit code.')
    parser.add_argument(
        '--exclude-exit-code', action='append', default=[], type=int,
        help='exclude command which finished with given exit code.')

    # Sorter
    parser = parent_parser.add_argument_group('Sorter')
    parser.add_argument(
        '--reverse', action='store_true', default=False,
        help="""
        Reverse order of the result.
        By default, most recent commands are shown.
        """)
    parser.add_argument(
        '--sort-by', default='count',
        choices=sorted(SORT_KEY_SYNONYMS),
        help="""
        Sort keys
        `count`: number of the time command is executed;
        `start`(=`time`): the time command is executed;
        `stop`: the time command is finished;
        `code`: exit code of the command;
        """)
    parser.add_argument(
        '--sort-by-program-frequency',
        help="""
        [NOT IMPLEMENTED]
        most used program comes first.
        """)

    # Modifier
    parser = parent_parser.add_argument_group('Modifier')
    parser.add_argument(
        '--after-context', type=int, metavar='NUM',
        help="""
        [NOT IMPLEMENTED]
        Print NUM commands executed after matching commands.
        """)
    parser.add_argument(
        '--before-context', type=int, metavar='NUM',
        help="""
        [NOT IMPLEMENTED]
        Print NUM commands executed before matching commands.
        """)
    parser.add_argument(
        '--context', type=int, metavar='NUM',
        help="""
        [NOT IMPLEMENTED]
        Print NUM commands executed before and after matching commands.
        """)
    parser.add_argument(
        '--context-type', choices=['session', 'time'],
        help="""
        [NOT IMPLEMENTED]
        `session`: commands executed in the same shell session;
        `time`: commands executed around the same time;
        """)

    # Formatter
    parser = parent_parser.add_argument_group('Formatter')
    parser.add_argument(
        '--with-command-id', action='store_true', default=False,
        help="""
        Print command ID number.
        When this is set, --format option has no effect.
        If --with-session-id is also specified, session ID comes
        at the first column then command ID comes the next column.
        """)
    parser.add_argument(
        '--with-session-id', action='store_true', default=False,
        help="""
        Print session ID number.
        When this is set, --format option has no effect.
        See also: --with-command-id
        """)
    parser.add_argument(
        '--format', default=r'{command}\n',
        help="""
        Python string formatter.  Available keys:
        command, exit_code, pipestatus (a list), start, stop, cwd,
        command_history_id, session_history_id.
        See also:
        http://docs.python.org/library/string.html#format-string-syntax
        """)

    # Misc
    parser = parent_parser.add_argument_group('Misc')
    parser.add_argument(
        '--output', default='-', type=argparse.FileType('w'),
        help="""
        Output file to write the results in. Default is stdout.
        """)


commands = [
    ('search', search_add_arguments, search_run),
]
