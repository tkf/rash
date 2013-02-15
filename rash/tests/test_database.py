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

from ..model import CommandRecord, SessionRecord
from ..database import DataBase, normalize_directory
from ..utils.py3compat import nested
from .utils import BaseTestCase, monkeypatch, izip_dict


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
        return os.path.join(os.path.sep, *ps)

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
        self.db.import_dict({})
        records = self.search_command_record()
        self.assert_same_command_record(records[0], to_command_record({}))
        self.assertEqual(len(records), 1)

    def test_import_command_record(self):
        data = self.get_dummy_command_record_data()
        self.db.import_dict(data)
        records = self.search_command_record()
        crec = records[0]
        self.assert_same_command_record(crec, to_command_record(data))
        self.assertEqual(len(records), 1)

    def test_import_command_record_no_check_duplicate(self):
        data = self.get_dummy_command_record_data()
        num = 3
        for _ in range(num):
            self.db.import_dict(data, check_duplicate=False)
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
            self.db.import_dict(data, check_duplicate=True)
        records = self.search_command_record(unique=False)
        self.assert_same_command_record(records[0], to_command_record(data))
        self.assertEqual(len(records), 1)

    def prepare_command_record(self, command=['git status', 'hg status'],
                               **kwds):
        def update(data, **kwds):
            for (k, v) in kwds.items():
                if v is not None:
                    data[k] = v
        records = []
        kwds.update(command=command)
        for dct in izip_dict(kwds):
            data = self.get_dummy_command_record_data()
            update(data, **dct)
            self.db.import_dict(data)
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
                self.db.import_dict(data)

        records = self.search_command_record(sort_by='command_count')
        self.assertEqual(len(records), 3)

        commands = [r.command for r in records]
        self.assertEqual(commands, ['command C', 'command A', 'command B'])

        counts = [r.command_count for r in records]
        self.assertEqual(counts, [15, 10, 5])

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
        for (i, environ) in enumerate(command_environ_list):
            data = self.get_dummy_command_record_data()
            data.update(command='command', start=i, environ=environ)
            self.db.import_dict(data)

        records = self.search_environ_record(
            include_pattern=[('PATH', 'DIR*')])
        self.assertEqual(len(records), 2)

        records = self.search_environ_record(
            include_pattern=[('PATH', 'DIR-1')])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].variable_name, 'PATH')
        self.assertEqual(records[0].variable_value, 'DIR-1')

    def test_serach_command_by_environ_in_command(self):
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        # Database does not distinguish record by different environ,
        # so other key must be different.
        data1['command'] = 'git status'
        data2['command'] = 'hg status'
        data1['environ'] = {'SHELL': 'zsh'}
        data2['environ'] = {'SHELL': 'bash'}
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

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
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        # Database does not distinguish record by different environ,
        # so other key must be different.
        data1['command'] = 'git status'
        data2['command'] = 'hg status'
        data1['environ'] = {'SHELL': 'zsh'}
        data2['environ'] = {'SHELL': 'bash'}
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

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

    def test_serach_command_by_environ_in_session(self):
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        # Database does not distinguish record by different environ,
        # so other key must be different.
        data1['command'] = 'git status'
        data2['command'] = 'hg status'
        data1['session_id'] = 'DUMMY-SESSION-ID-1'
        data2['session_id'] = 'DUMMY-SESSION-ID-2'
        # FIXME: Make the test pass without setting data1['environ'] = {}.
        # The test with exclude_environ_pattern=[('SHELL', 'zsh')] fails
        # because EV table selects these non-relevant environment variables
        # in data1['environ'] and data2['environ'].
        data1['environ'] = {}
        data2['environ'] = {}
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

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
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        # Database does not distinguish record by different environ,
        # so other key must be different.
        data1['command'] = 'git status'
        data2['command'] = 'hg status'
        data1['session_id'] = 'DUMMY-SESSION-ID-1'
        data2['session_id'] = 'DUMMY-SESSION-ID-2'
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

        init_data_1 = {'session_id': 'DUMMY-SESSION-ID-1',
                       'environ': {'SHELL': 'zsh'}}
        init_data_2 = {'session_id': 'DUMMY-SESSION-ID-2',
                       'environ': {'SHELL': 'bash'}}
        self.db.import_init_dict(init_data_1)
        self.db.import_init_dict(init_data_2)

        records = self.search_command_record(
            include_glob_environ=[('SHELL', '*sh')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assert_same_command_record(records[1], dcrec2)
        self.assertEqual(len(records), 2)

        records = self.search_command_record(
            include_environ_pattern=[('SHELL', 'sh*')], unique=False)
        self.assertEqual(len(records), 0)

        records = self.search_command_record(
            exclude_environ_pattern=[('SHELL', 'sh*')], unique=False)
        self.assertEqual(len(records), 2)

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
        self.db.import_dict(command_data)

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

        self.db.import_dict(command_data)
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

        self.db.import_dict(command_data_1)
        self.db.import_dict(command_data_2)
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
        self.db.import_dict(command_data)

        records = self.search_command_record()
        self.assertEqual(len(records), 1)
        command_history_id = records[0].command_history_id

        crec = self.db.get_full_command_record(command_history_id)
        self.assertEqual(crec.pipestatus, command_data['pipestatus'])
