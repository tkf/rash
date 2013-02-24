# Copyright (C) 2013-  Takafumi Arakaki

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import datetime
import itertools
import string
import operator

from ..model import CommandRecord, SessionRecord
from ..database import DataBase, normalize_directory
from ..utils.py3compat import nested
from .utils import BaseTestCase, monkeypatch, zip_dict


def setdefaults(d, **kwds):
    for (k, v) in kwds.items():
        d.setdefault(k, v)


def to_sql_timestamp(ts):
    if ts is not None:
        dt = datetime.datetime.utcfromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def to_record(recclass, data):
    crec = recclass(**data)
    crec.start = to_sql_timestamp(crec.start)
    crec.stop = to_sql_timestamp(crec.stop)
    return crec


def to_command_record(data):
    crec = to_record(CommandRecord, data)
    crec.cwd = normalize_directory(crec.cwd)
    return crec


def to_session_record(data):
    return to_record(SessionRecord, data)


def update_nonnones(data, **kwds):
    for (k, v) in kwds.items():
        if v is not None:
            data[k] = v


def attrs(objects, attr):
    """Get attribute `attr` of each object in `objects`."""
    return list(map(operator.attrgetter(attr), objects))


class InMemoryDataBase(DataBase):

    def __init__(self):
        import sqlite3
        db = sqlite3.connect(':memory:')
        self._get_db = lambda: db
        self._init_db()
        self.update_version_records()


class TestInMemoryDataBase(BaseTestCase):

    dbclass = InMemoryDataBase

    def abspath(self, *ps):
        # SOMEDAY: Remove TestInMemoryDataBase.abspath.
        #          All paths in test should be written in posix way.
        return os.path.join(os.path.sep, *ps)

    @staticmethod
    def adapt_file_path(path, _sep=os.path.sep):
        """
        Convert slash-separated path to OS-specific one.
        """
        return _sep.join(path.split('/'))

    @classmethod
    def adapt_file_path_in_dict(cls, kwds):
        """
        Convert slash-separated paths in `kwds` to OS-specific one.
        """
        for key in ['cwd', 'cwd_glob', 'cwd_under',
                    'sort_by_cwd_distance']:
            val = kwds.get(key)
            if not val:
                continue
            if isinstance(val, (list, tuple)):
                kwds[key] = list(map(cls.adapt_file_path, val))
            else:
                kwds[key] = cls.adapt_file_path(val)

    def setUp(self):
        self.db = self.dbclass()

    def test_info_get_version(self):
        from ..__init__ import __version__
        from ..database import schema_version
        verrec = next(self.db.get_version_records())
        self.assertEqual(verrec.rash_version, __version__)
        self.assertEqual(verrec.schema_version, schema_version)

    def test_info_version_update(self):
        from .. import __init__
        from .. import database
        new_project_ver = '100.0.0'
        new_schema_ver = '100.0.0'
        with nested(monkeypatch(__init__, '__version__', new_project_ver),
                    monkeypatch(database, 'schema_version', new_schema_ver)):
            self.db.update_version_records()
        records = list(self.db.get_version_records())
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].rash_version, new_project_ver)
        self.assertEqual(records[0].schema_version, new_schema_ver)
        self.assertEqual(records[1].rash_version, __init__.__version__)
        self.assertEqual(records[1].schema_version, database.schema_version)

    def import_command_record(self, data, **kwds):
        self.adapt_file_path_in_dict(data)
        self.db.import_dict(data, **kwds)

    def get_default_search_kwds(self):
        import argparse
        from ..search import search_add_arguments
        from ..query import preprocess_kwds
        parser = argparse.ArgumentParser()
        search_add_arguments(parser)
        kwds = vars(parser.parse_args([]))
        return preprocess_kwds(kwds)

    def search_command_record(self, **kwds):
        setdefaults(kwds, **self.get_default_search_kwds())
        self.adapt_file_path_in_dict(kwds)
        return list(self.db.search_command_record(**kwds))

    def assert_same_command_record(
            self, crec1, crec2,
            keys=['command', 'cwd', 'terminal', 'start', 'stop', 'exit_code']):
        asdict = lambda rec: dict((k, getattr(rec, k)) for k in keys)
        self.assertEqual(asdict(crec1), asdict(crec2))

    def assert_not_same_command_record(self, *args, **kwds):
        self.assertRaises(AssertionError, self.assert_same_command_record,
                          *args, **kwds)

    def get_dummy_command_record_data(self):
        return {
            'command': 'DUMMY COMMAND',
            'cwd': self.abspath('DUMMY', 'WORKING', 'DIRECTORY'),
            'exit_code': 0,
            'pipestatus': [2, 3, 0],
            'start': 100,
            'stop': 102,
            'terminal': 'DUMMY_TERMINAL',
            'session_id': 'DUMMY-SESSION-ID',
            'environ': {
                'PATH': 'DUMMY:PATH:DATA',
            },
        }

    def test_empty_database(self):
        records = self.search_command_record()
        self.assertEqual(len(records), 0)

    def test_import_empty_command_record(self):
        self.import_command_record({})
        records = self.search_command_record()
        self.assert_same_command_record(records[0], to_command_record({}))
        self.assertEqual(len(records), 1)

    def test_import_command_record(self):
        data = self.get_dummy_command_record_data()
        self.import_command_record(data)
        records = self.search_command_record()
        crec = records[0]
        self.assert_same_command_record(crec, to_command_record(data))
        self.assertEqual(len(records), 1)

    def test_import_command_record_no_check_duplicate(self):
        data = self.get_dummy_command_record_data()
        num = 3
        for _ in range(num):
            self.import_command_record(data, check_duplicate=False)
        records = self.search_command_record(unique=False)
        for crec in records:
            self.assert_same_command_record(crec, to_command_record(data))
        self.assertEqual(len(records), num)

    def test_import_command_record_check_duplicate(self):
        data = self.get_dummy_command_record_data()
        # Import different version of data which DB cannot distinguish.
        for env in [{'SHELL': 'bash'}, {'SHELL': 'zsh'},
                    {'SHELL': 'tcsh'}, {'SHELL': 'sh'}]:
            data['environ'].update(env)
            self.import_command_record(data, check_duplicate=True)
        records = self.search_command_record(unique=False)
        self.assert_same_command_record(records[0], to_command_record(data))
        self.assertEqual(len(records), 1)

    def prepare_command_history_table(self, keys, lists):
        """
        Import command records specified by values in `lists`.

        `i`-th record will be generated by a dict::

            dict(zip(keys, lists[i]))

        If key is missing or None, it is complemented by
        :meth:`get_dummy_command_record_data`.

        :rtype: list of CommandRecord

        """
        records = []
        for (i, vals) in enumerate(lists):
            data = self.get_dummy_command_record_data()
            update_nonnones(data, **dict(zip(keys, vals)))
            if 'start' not in keys:
                data['start'] = i
            self.import_command_record(data)
            records.append(to_command_record(data))
        return records

    def prepare_command_record(self, command=['git status', 'hg status'],
                               **kwds):
        """
        Import command records specified by `kwds`.

        The keyword argument is same as the one used in command record.
        But its value is a list instead of actual value.  The values in
        the list is zipped and mixed in the dummy command record data
        and imported to the test DB.

        :rtype: list of CommandRecord

        """
        records = []
        kwds.update(command=command)
        for dct in zip_dict(kwds):
            data = self.get_dummy_command_record_data()
            update_nonnones(data, **dct)
            self.import_command_record(data)
            records.append(to_command_record(data))
        return records

    def test_search_command_by_pattern(self):
        (dcrec1, dcrec2) = self.prepare_command_record()

        records = self.search_command_record(include_pattern=['git*'],
                                             unique=False)
        crec = records[0]
        self.assert_same_command_record(crec, dcrec1)
        self.assert_not_same_command_record(crec, dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(include_pattern=['bzr*'],
                                             unique=False)
        self.assertEqual(len(records), 0)

    def test_search_command_by_exclude_pattern(self):
        (dcrec1, dcrec2) = self.prepare_command_record()

        records = self.search_command_record(exclude_pattern=['hg*'],
                                             unique=False)
        crec = records[0]
        self.assert_same_command_record(crec, dcrec1)
        self.assert_not_same_command_record(crec, dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(exclude_pattern=['bzr*'],
                                             unique=False)
        self.assertEqual(len(records), 2)

    def test_search_command_by_complex_pattern(self):
        (dcrec1, dcrec2) = self.prepare_command_record()

        records = self.search_command_record(
            include_pattern=['*status'], exclude_pattern=['hg*'],
            unique=False)
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], dcrec1)

        records = self.search_command_record(
            include_pattern=['hg*'], exclude_pattern=['*status'],
            unique=False)
        self.assertEqual(len(records), 0)

    def test_search_command_by_pattern_ignore_case(self):
        self.prepare_command_record(
            [f('command') for f in [str.lower, str.upper, str.capitalize]])

        # Default search is case-sensitive
        records = self.search_command_record(include_pattern=['command'],
                                             unique=False)
        self.assertEqual(len(records), 1)

        # Perform case-insensitive search
        records = self.search_command_record(include_pattern=['command'],
                                             ignore_case=True,
                                             unique=False)
        self.assertEqual(len(records), 3)

    def test_search_command_by_regexp(self):
        (dcrec1, dcrec2) = self.prepare_command_record()

        records = self.search_command_record(match_regexp=['g.*', '.*st.*'],
                                             unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(include_regexp=['git.*'],
                                             unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(exclude_regexp=['git.*'],
                                             unique=False)
        self.assert_same_command_record(records[0], dcrec2)
        self.assertEqual(len(records), 1)

    def test_search_command_by_cwd(self):
        cwd_list = [self.abspath('DUMMY', 'A'), self.abspath('DUMMY', 'B')]
        (dcrec1, dcrec2) = self.prepare_command_record(cwd=cwd_list)

        records = self.search_command_record(cwd=[cwd_list[0]], unique=False)
        crec = records[0]
        self.assert_same_command_record(crec, dcrec1)
        self.assert_not_same_command_record(crec, dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(cwd=[self.abspath('DUMMY')],
                                             unique=False)
        self.assertEqual(len(records), 0)

    def test_search_command_by_cwd_glob(self):
        cwd_list = [self.abspath('DUMMY', 'A'), self.abspath('DUMMY', 'B')]
        (dcrec1, dcrec2) = self.prepare_command_record(cwd=cwd_list)

        records = self.search_command_record(
            cwd_glob=[self.abspath('DUMMY', '*')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assert_same_command_record(records[1], dcrec2)
        self.assertEqual(len(records), 2)

        records = self.search_command_record(
            cwd_glob=[self.abspath('REAL', '*')], unique=False)
        self.assertEqual(len(records), 0)

    def test_search_command_sort_by_command_count(self):
        command_num_pairs = [('command A', 10),
                             ('command B', 5),
                             ('command C', 15)]
        for (command, num) in command_num_pairs:
            for i in range(num):
                data = self.get_dummy_command_record_data()
                data.update(
                    command=command,
                    # Use `start` to make the record unique
                    start=i)
                self.import_command_record(data)

        records = self.search_command_record(sort_by=['command_count'])
        self.assertEqual(len(records), 3)

        commands = [r.command for r in records]
        self.assertEqual(commands, ['command C', 'command A', 'command B'])

        counts = [r.command_count for r in records]
        self.assertEqual(counts, [15, 10, 5])

    def prepare_command_record_from_exit_codes(self, exit_codes):
        commands = ['COMMAND-{0}'.format(i)
                    for (i, codes) in enumerate(exit_codes) for _ in codes]
        self.prepare_command_record(command=commands,
                                    exit_code=itertools.chain(*exit_codes),
                                    start=range(len(commands)))

    def test_search_command_sort_by_success_count(self):
        self.prepare_command_record_from_exit_codes([[0, 1, 2, 0], [0, 0, 0]])

        records = self.search_command_record(sort_by=['success_count'])
        self.assertEqual(len(records), 2)

        attrs = lambda key: [getattr(r, key) for r in records]
        self.assertEqual(attrs('command'), ['COMMAND-1', 'COMMAND-0'])
        self.assertEqual(attrs('success_count'), [3, 2])
        self.assertEqual(attrs('success_ratio'), [1.0, 0.5])

    def test_search_command_sort_by_success_ratio(self):
        self.prepare_command_record_from_exit_codes([[0, 1, 2, 0],
                                                     [1, 2, 3],
                                                     [0, 0, 0]])

        records = self.search_command_record(sort_by=['success_ratio'])
        self.assertEqual(len(records), 3)

        attrs = lambda key: [getattr(r, key) for r in records]
        self.assertEqual(attrs('command'),
                         ['COMMAND-2', 'COMMAND-0', 'COMMAND-1'])
        self.assertEqual(attrs('success_count'), [3, 2, 0])
        self.assertEqual(attrs('success_ratio'), [1.0, 0.5, 0.0])

    def test_search_command_sort_by_cwd_distance(self):
        command_list = [
            'A',
            'AB',
            'ABC',
            'ABCD',
            'ABX',
        ]
        # for simplicity, cwd for ABC is /A/B/C/
        cwd_list = [self.abspath(*x) for x in command_list]
        self.prepare_command_record(command=command_list, cwd=cwd_list,
                                    start=reversed(range(len(command_list))))

        records = self.search_command_record(
            sort_by_cwd_distance=self.abspath('A', 'B', 'C'),
            # do disambiguate order, sort by start time also.
            sort_by=['start_time'])
        record_commands = [r.command for r in records]
        record_cwd_distances = [r.cwd_distance for r in records]
        self.assertEqual(record_commands, ['ABC', 'AB', 'ABCD', 'ABX', 'A'])
        self.assertEqual(record_cwd_distances, [0, 1, 1, 1, 2])

    def test_search_command_sort_by_ambiguous_cwd_distance(self):
        """
        Minimum `cwd_distance` must be chosen.

        When same command is executed at different directories,
        the value of `cwd_distance` is ambiguous.

        """
        self.prepare_command_history_table(
            ['command', 'cwd'],
            [['c-0',    '/A/B/C'],
             ['c-0',    '/A/B'],
             ['c-0',    '/A'],
             ['c-1',    '/A'],
             ['c-2',    '/A/B'],
             ['c-2',    '/A/B/C/D/E']])

        records = self.search_command_record(
            sort_by_cwd_distance='/A/B/C',
            # do disambiguate order, sort by start time also.
            sort_by=['start_time'])
        self.assertEqual(attrs(records, 'command'), ['c-0', 'c-2', 'c-1'])
        self.assertEqual(attrs(records, 'cwd_distance'), [0, 1, 2])

    def test_search_command_with_connection(self):
        num = 5
        small_num = 3
        self.prepare_command_record(map('COMMAND-{0}'.format, range(num)))

        kwds = dict(unique=False)
        setdefaults(kwds, **self.get_default_search_kwds())

        # Generator hold connection to DB
        records = self.db.search_command_record(**kwds)
        self.assertEqual(len(list(records)), num)

        # Generator can be resumed
        records = self.db.search_command_record(**kwds)
        first_half = list(itertools.islice(records, small_num))
        second_half = list(records)
        self.assertEqual(len(first_half), small_num)
        self.assertEqual(len(second_half), num - small_num)

        # Generator stops if the connection is closed
        records = self.db.search_command_record(**kwds)
        first_half = list(itertools.islice(records, small_num))
        self.db.close_connection()
        second_half = list(records)
        self.assertEqual(len(first_half), small_num)
        self.assertEqual(len(second_half), 0)

    def search_environ_record(self, **kwds):
        return list(self.db.search_environ_record(**kwds))

    def test_search_environ_by_pattern(self):
        command_environ_list = [
            {'PATH': 'DIR-1'},
            {'PATH': 'DIR-2', 'PYTHONPATH': 'DIR-1'},
        ]
        self.prepare_command_record(environ=command_environ_list,
                                    start=range(len(command_environ_list)))

        records = self.search_environ_record(
            include_pattern=[('PATH', 'DIR*')])
        self.assertEqual(len(records), 2)

        records = self.search_environ_record(
            include_pattern=[('PATH', 'DIR-1')])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].variable_name, 'PATH')
        self.assertEqual(records[0].variable_value, 'DIR-1')

    def test_serach_command_by_environ_in_command(self):
        (dcrec1, dcrec2) = self.prepare_command_record(
            environ=[{'SHELL': 'zsh'}, {'SHELL': 'bash'}])

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'zsh')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'zsh')], unique=False)
        self.assert_same_command_record(records[0], dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'sh')], unique=False)
        self.assertEqual(len(records), 0)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'sh')], unique=False)
        self.assertEqual(len(records), 2)

    def test_serach_command_by_glob_environ_in_command(self):
        (dcrec1, dcrec2) = self.prepare_command_record(
            environ=[{'SHELL': 'zsh'}, {'SHELL': 'bash'}])

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', '*sh')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assert_same_command_record(records[1], dcrec2)
        self.assertEqual(len(records), 2)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'sh*')], unique=False)
        self.assertEqual(len(records), 0)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'sh*')], unique=False)
        self.assertEqual(len(records), 2)

    def import_dummy_sessions(self, num=10):
        """
        Insert dummy non-empty sessions.

        This is to make sure that command_history.id and session_id
        are different.  Call this function before importing command
        records.

        """
        for i in range(num):
            self.db.import_init_dict({'session_id': 'DUMMY-ID-{0}'.format(i)})

    def test_serach_command_by_environ_in_session(self):
        self.import_dummy_sessions()
        sessions = ['DUMMY-SESSION-ID-1', 'DUMMY-SESSION-ID-2']
        (dcrec1, dcrec2) = self.prepare_command_record(session_id=sessions)

        init_data_1 = {'session_id': 'DUMMY-SESSION-ID-1',
                       'environ': {'SHELL': 'zsh'}}
        init_data_2 = {'session_id': 'DUMMY-SESSION-ID-2',
                       'environ': {'SHELL': 'bash'}}
        self.db.import_init_dict(init_data_1)
        self.db.import_init_dict(init_data_2)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'zsh')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'zsh')], unique=False)
        self.assert_same_command_record(records[0], dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'sh')], unique=False)
        self.assertEqual(len(records), 0)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'sh')], unique=False)
        self.assertEqual(len(records), 2)

    def test_serach_command_by_glob_environ_in_session(self):
        self.import_dummy_sessions()
        sessions = ['DUMMY-SESSION-ID-1', 'DUMMY-SESSION-ID-2']
        (dcrec1, dcrec2) = self.prepare_command_record(session_id=sessions)

        init_data_1 = {'session_id': 'DUMMY-SESSION-ID-1',
                       'environ': {'SHELL': 'zsh'}}
        init_data_2 = {'session_id': 'DUMMY-SESSION-ID-2',
                       'environ': {'SHELL': 'bash'}}
        self.db.import_init_dict(init_data_1)
        self.db.import_init_dict(init_data_2)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', '*sh')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assert_same_command_record(records[1], dcrec2)
        self.assertEqual(len(records), 2)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'sh*')], unique=False)
        self.assertEqual(len(records), 0)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'sh*')], unique=False)
        self.assertEqual(len(records), 2)

    def test_serach_command_by_glob_and_regexp_environ(self):
        stride = 3
        num = 10
        environ = [{'E1': string.ascii_lowercase[i: i + stride],
                    'E2': string.ascii_uppercase[i: i + stride]}
                   for i in range(num)]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ)

        records = self.search_command_record(
            include_environ_pattern=[('E1', '*a*')],
            include_environ_regexp=[('E2', 'A..')],
            unique=False)
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], drecs[0])

    def test_serach_command_by_and_match_environ(self):
        ev_table = [
            ['EV0', 'EV1', 'EV2'],
            ['abc', 'bcd', 'cde'],  # \ <------------ #match = 1
            ['bcd', 'cde', 'def'],  # | <-- #include = 3
            ['cde', 'def', 'efg'],  # /
            ['def', 'efg', 'fgh'],
        ]
        environ = [dict(zip(ev_table[0], vs)) for vs in ev_table[1:]]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ)

        params = [('EV0', '*c*'),
                  ('EV1', '*c*'),
                  ('EV2', '*c*')]

        # "include" selects many records:
        records = self.search_command_record(include_environ_pattern=params)
        self.assertEqual(len(records), 3)

        # Using the same parameter, "match" selects only one record:
        records = self.search_command_record(match_environ_pattern=params)
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], drecs[0])

        records = self.search_command_record(
            match_environ_pattern=[('EV0', '*a*'),
                                   ('EV2', '*f*')],
            unique=False)
        self.assertEqual(len(records), 0)

    def test_serach_command_by_and_match_session_environ(self):
        sessions = list(map('SESSION-{0}'.format, range(2)))
        table = [
            (['EV0', 'EV1', 'EV2'], 'Session ID'),
            (['abc', 'bcd', 'cde'], sessions[0]),
            (['bcd', 'cde', 'def'], sessions[0]),
            (['cde', 'def', 'efg'], sessions[1]),
            (['def', 'efg', 'fgh'], sessions[1]),
        ]
        environ = [dict(zip(table[0][0], vs)) for (vs, _) in table[1:]]
        session_id = [sid for (_, sid) in table[1:]]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ, session_id=session_id)

        init_data_1 = {'session_id': sessions[0],
                       'environ': {'SHELL': 'zsh'}}
        init_data_2 = {'session_id': sessions[1],
                       'environ': {'SHELL': 'bash'}}
        self.db.import_init_dict(init_data_1)
        self.db.import_init_dict(init_data_2)

        records = self.search_command_record(
            match_environ_pattern=[('EV1', '*e*'),
                                   ('SHELL', 'zsh')],
            unique=False)
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], drecs[1])

        records = self.search_command_record(
            match_environ_pattern=[('EV1', '*d*'),
                                   ('SHELL', 'zsh')],
            unique=False)
        self.assertEqual(len(records), 2)
        self.assert_same_command_record(records[0], drecs[0])
        self.assert_same_command_record(records[1], drecs[1])

    def test_serach_command_by_complex_environ_match(self):
        ev_table = [
            ['EV0', 'EV1', 'EV2'],
            ['abc', 'bcd', 'cde'],  # |M0|  |E0 |  |
            ['bcd', 'cde', 'def'],  # |M0|I0|E0 |E1|  <- match!
            ['cde', 'def', 'efg'],  # |M0|I0|   |E1|
            ['def', 'efg', 'fgh'],  # |  |I0|E0 |E1|
        ]
        environ = [dict(zip(ev_table[0], vs)) for vs in ev_table[1:]]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(command=command, environ=environ)

        records = self.search_command_record(
            match_environ_pattern=[('EV0', '*c*')],                  # M0
            include_environ_pattern=[('EV2', '*f*')],                # I0
            exclude_environ_pattern=[('EV0', 'c*'), ('EV2', 'c*')],  # E0, E1
        )
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], drecs[1])

    def test_serach_command_by_environ_same_name_in_session(self):
        sessions = list(map('SESSION-{0}'.format, range(2)))
        environ = [{'PATH': 'a:b:c'},  # session 0
                   {'PATH': 'a:b:X'},  # session 1
                   {'PATH': 'a:X:c'},  # session 0
                   {'PATH': 'X:b:c'}]  # session 1
        session_id = sessions * 2
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ, session_id=session_id)

        init_data_1 = {'session_id': sessions[0],
                       'environ': {'PATH': 'X:Y:Z'}}
        init_data_2 = {'session_id': sessions[1],
                       'environ': {'PATH': 'U:V:W'}}
        self.db.import_init_dict(init_data_1)
        self.db.import_init_dict(init_data_2)

        records = self.search_command_record(
            match_environ_pattern=[('PATH', '*X*')],
        )
        self.assertEqual(len(records), 4)

        records = self.search_command_record(
            match_environ_pattern=[('PATH', 'X*')],
        )
        self.assertEqual(len(records), 3)
        self.assert_same_command_record(records[0], drecs[0])
        self.assert_same_command_record(records[1], drecs[2])
        self.assert_same_command_record(records[2], drecs[3])

        records = self.search_command_record(
            match_environ_pattern=[('PATH', 'X*'), ('PATH', 'a*')],
        )
        self.assertEqual(len(records), 2)
        self.assert_same_command_record(records[0], drecs[0])
        self.assert_same_command_record(records[1], drecs[2])

    def test_serach_command_by_environ_regexp_match(self):
        ev_table = [
            ['EV0', 'EV1', 'EV2'],
            ['abc', 'bcd', 'cde'],
            ['bcd', 'cde', 'def'],
            ['cde', 'def', 'efg'],
            ['def', 'efg', 'fgh'],
        ]
        environ = [dict(zip(ev_table[0], vs)) for vs in ev_table[1:]]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ)

        records = self.search_command_record(
            match_environ_regexp=[('EV0', 'c..|..c'), ('EV1', '.?e.*')],
        )
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], drecs[2])

    def test_serach_command_by_environ_regexp_include(self):
        ev_table = [
            ['EV0', 'EV1', 'EV2'],
            ['abc', 'bcd', 'cde'],
            ['bcd', 'cde', 'def'],
            ['cde', 'def', 'efg'],
            ['def', 'efg', 'fgh'],
        ]
        environ = [dict(zip(ev_table[0], vs)) for vs in ev_table[1:]]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ)

        records = self.search_command_record(
            include_environ_regexp=[('EV0', 'c..|..c'), ('EV1', '.?e.*')],
            sort_by=['command'], reverse=True)
        self.assertEqual(len(records), 3)
        self.assert_same_command_record(records[0], drecs[0])
        self.assert_same_command_record(records[1], drecs[2])
        self.assert_same_command_record(records[2], drecs[3])

    def test_serach_command_by_environ_regexp_exclude(self):
        ev_table = [
            ['EV0', 'EV1', 'EV2'],
            ['abc', 'bcd', 'cde'],
            ['bcd', 'cde', 'def'],
            ['cde', 'def', 'efg'],
            ['def', 'efg', 'fgh'],
        ]
        environ = [dict(zip(ev_table[0], vs)) for vs in ev_table[1:]]
        command = list(map('COMMAND-{0}'.format, range(len(environ))))
        drecs = self.prepare_command_record(
            command=command, environ=environ)

        records = self.search_command_record(
            exclude_environ_regexp=[('EV0', 'c..|..c'), ('EV1', '.?e.*')],
        )
        self.assertEqual(len(records), 1)
        self.assert_same_command_record(records[0], drecs[1])

    def test_serach_command_with_time_context(self):
        command = [
            'c-0',
            'c-1-match',
            'c-2',
            'c-3',
            'c-4',
            'c-5-match',
            'c-6',
        ]
        self.prepare_command_record(command=command, start=range(len(command)))

        # --context 1
        records = self.search_command_record(include_pattern=['*match'],
                                             context=1)
        result_command = list(reversed([r.command for r in records]))
        self.assertEqual(result_command, command[:3] + command[4:])

        # --before-context 1
        records = self.search_command_record(include_pattern=['*match'],
                                             before_context=1)
        result_command = [r.command for r in records]
        self.assertEqual(result_command, ['c-5-match', 'c-4',
                                          'c-1-match', 'c-0'])

        # --after-context 1
        records = self.search_command_record(include_pattern=['*match'],
                                             after_context=1)
        result_command = [r.command for r in records]
        self.assertEqual(result_command, ['c-6', 'c-5-match',
                                          'c-2', 'c-1-match'])

    def test_serach_command_with_session_context(self):
        command = [
            'c-0',
            'c-1-match',
            'c-2',
            'c-3',
            'c-4',
            'c-5-match',
            'c-6',
        ]
        session_id = ['S-0'] * 4 + ['S-1'] * 3
        self.prepare_command_record(command=command, start=range(len(command)),
                                    session_id=session_id)
        self.db.import_init_dict({'session_id': 'S-0', 'start': 1})
        self.db.import_init_dict({'session_id': 'S-1', 'start': 0})

        # --context 1
        records = self.search_command_record(include_pattern=['*match'],
                                             context=1,
                                             context_type='session')
        result_command = list(reversed([r.command for r in records]))
        self.assertEqual(result_command, command[4:] + command[:3])

        # --before-context 1
        records = self.search_command_record(include_pattern=['*match'],
                                             before_context=1,
                                             context_type='session')
        result_command = [r.command for r in records]
        self.assertEqual(result_command, ['c-1-match', 'c-0',
                                          'c-5-match', 'c-4'])

        # --after-context 1
        records = self.search_command_record(include_pattern=['*match'],
                                             after_context=1,
                                             context_type='session')
        result_command = [r.command for r in records]
        self.assertEqual(result_command, ['c-2', 'c-1-match',
                                          'c-6', 'c-5-match'])

    def search_session_record(self, **kwds):
        return list(self.db.search_session_record(**kwds))

    def assert_same_session_record(
            self, srec1, srec2, keys=['session_id', 'start', 'stop']):
        asdict = lambda rec: dict((k, getattr(rec, k)) for k in keys)
        self.assertEqual(asdict(srec1), asdict(srec2))

    def assert_not_same_session_record(self, *args, **kwds):
        self.assertRaises(AssertionError, self.assert_same_session_record,
                          *args, **kwds)

    def test_import_init_record_and_then_exit_record(self):
        session_id = 'DUMMY-SESSION-ID'
        init_data = {'session_id': session_id, 'start': 100}
        exit_data = {'session_id': session_id, 'stop': 102}
        self.db.import_init_dict(init_data)
        self.db.import_exit_dict(exit_data)

        session_data = {}
        session_data.update(init_data)
        session_data.update(exit_data)

        records = self.search_session_record(session_id=session_id)
        self.assert_same_session_record(records[0],
                                        to_session_record(session_data))
        self.assertEqual(len(records), 1)

    def test_import_exit_record_and_then_init_record(self):
        session_id = 'DUMMY-SESSION-ID'
        init_data = {'session_id': session_id, 'start': 100}
        exit_data = {'session_id': session_id, 'stop': 102}
        self.db.import_exit_dict(exit_data)
        self.db.import_init_dict(init_data)

        session_data = {}
        session_data.update(init_data)
        session_data.update(exit_data)

        records = self.search_session_record(session_id=session_id)
        self.assert_same_session_record(records[0],
                                        to_session_record(session_data))
        self.assertEqual(len(records), 1)

    def test_import_session_record_with_environ(self):
        session_id = 'DUMMY-SESSION-ID'
        init_data = {'session_id': session_id, 'start': 100}
        exit_data = {'session_id': session_id, 'stop': 102}
        init_data['environ'] = {'SHELL': 'zsh'}
        self.db.import_init_dict(init_data)
        self.db.import_exit_dict(exit_data)

        session_data = {}
        session_data.update(init_data)
        session_data.update(exit_data)

        records = self.search_session_record(session_id=session_id)
        self.assert_same_session_record(records[0],
                                        to_session_record(session_data))
        self.assertEqual(len(records), 1)

    def check_consistency_one_command_in_one_session(self):
        session_id = 'DUMMY-SESSION-ID'
        session_records = self.search_session_record(session_id=session_id)
        sh_id = session_records[0].session_history_id
        self.assertIsInstance(sh_id, int)
        command_records = self.search_command_record(
            include_session_history_id=sh_id)
        self.assertEqual(sh_id, command_records[0].session_history_id)

    def test_import_session_record_after_command_record(self):
        self.test_import_command_record()
        self.test_import_exit_record_and_then_init_record()
        self.check_consistency_one_command_in_one_session()

    def test_import_session_record_before_command_record(self):
        self.test_import_exit_record_and_then_init_record()
        self.test_import_command_record()
        self.check_consistency_one_command_in_one_session()

    def test_get_full_command_record_simple_keys(self):
        command_data = self.get_dummy_command_record_data()
        self.import_command_record(command_data)

        records = self.search_command_record()
        self.assertEqual(len(records), 1)
        command_history_id = records[0].command_history_id

        crec = self.db.get_full_command_record(command_history_id)
        self.assert_same_command_record(crec, to_command_record(command_data))

    def test_get_full_command_record_merging_session_environ(self):
        session_id = 'DUMMY-SESSION-ID'
        init_data = {'session_id': session_id, 'start': 100}
        init_data['environ'] = {'SHELL': 'zsh'}
        command_data = self.get_dummy_command_record_data()
        command_data['session_id'] = session_id

        desired_environ = {}
        desired_environ.update(command_data['environ'])
        desired_environ.update(init_data['environ'])

        self.import_command_record(command_data)
        self.db.import_init_dict(init_data)

        records = self.search_command_record()
        self.assertEqual(len(records), 1)
        command_history_id = records[0].command_history_id

        crec = self.db.get_full_command_record(command_history_id)
        self.assertEqual(crec.environ, desired_environ)

        crec = self.db.get_full_command_record(command_history_id,
                                               merge_session_environ=False)
        self.assertEqual(crec.environ, command_data['environ'])

    def test_get_full_command_record_no_environ_leak(self):
        session_id_1 = 'DUMMY-SESSION-ID-1'
        session_id_2 = 'DUMMY-SESSION-ID-2'
        init_data_1 = {'session_id': session_id_1, 'start': 100}
        init_data_2 = {'session_id': session_id_2, 'start': 100}
        init_data_1['environ'] = {'SHELL': 'zsh'}
        init_data_2['environ'] = {'SHELL': 'bash'}
        command_data_1 = self.get_dummy_command_record_data()
        command_data_2 = self.get_dummy_command_record_data()
        command_data_1['session_id'] = session_id_1
        command_data_2['session_id'] = session_id_2

        desired_environ = {}
        desired_environ.update(command_data_1['environ'])
        desired_environ.update(init_data_1['environ'])

        self.import_command_record(command_data_1)
        self.import_command_record(command_data_2)
        self.db.import_init_dict(init_data_1)
        self.db.import_init_dict(init_data_2)

        records = list(self.db.select_by_command_record(
            to_command_record(command_data_1)))
        self.assertEqual(len(records), 1)
        command_history_id = records[0].command_history_id

        crec = self.db.get_full_command_record(command_history_id)
        self.assertEqual(crec.environ, desired_environ)

    def test_get_full_command_record_pipestatus(self):
        command_data = self.get_dummy_command_record_data()
        command_data['pipestatus'] = [2, 3, 0]
        self.import_command_record(command_data)

        records = self.search_command_record()
        self.assertEqual(len(records), 1)
        command_history_id = records[0].command_history_id

        crec = self.db.get_full_command_record(command_history_id)
        self.assertEqual(crec.pipestatus, command_data['pipestatus'])
