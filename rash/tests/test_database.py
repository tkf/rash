import os
import datetime

from ..model import CommandRecord, SessionRecord
from ..database import DataBase, normalize_directory
from .utils import BaseTestCase


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


class TestInMemoryDataBase(BaseTestCase):

    dbclass = InMemoryDataBase

    def abspath(self, *ps):
        return os.path.join(os.path.sep, *ps)

    def setUp(self):
        self.db = self.dbclass()

    def get_default_search_kwds(self):
        import argparse
        from ..search import search_add_arguments
        parser = argparse.ArgumentParser()
        search_add_arguments(parser)
        kwds = vars(parser.parse_args([]))
        return kwds

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

    def test_serach_command_by_pattern(self):
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        data1['command'] = 'git status'
        data2['command'] = 'hg status'
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

        records = self.search_command_record(pattern=['git*'], unique=False)
        crec = records[0]
        self.assert_same_command_record(crec, dcrec1)
        self.assert_not_same_command_record(crec, dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(pattern=['bzr*'], unique=False)
        self.assertEqual(len(records), 0)

    def test_serach_command_by_cwd(self):
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        data1['cwd'] = self.abspath('DUMMY', 'A')
        data2['cwd'] = self.abspath('DUMMY', 'B')
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

        records = self.search_command_record(cwd=[data1['cwd']], unique=False)
        crec = records[0]
        self.assert_same_command_record(crec, dcrec1)
        self.assert_not_same_command_record(crec, dcrec2)
        self.assertEqual(len(records), 1)

        records = self.search_command_record(cwd=[self.abspath('DUMMY')],
                                             unique=False)
        self.assertEqual(len(records), 0)

    def test_serach_command_by_cwd_glob(self):
        data1 = self.get_dummy_command_record_data()
        data2 = self.get_dummy_command_record_data()
        data1['cwd'] = self.abspath('DUMMY', 'A')
        data2['cwd'] = self.abspath('DUMMY', 'B')
        self.db.import_dict(data1)
        self.db.import_dict(data2)
        dcrec1 = to_command_record(data1)
        dcrec2 = to_command_record(data2)

        records = self.search_command_record(
            cwd_glob=[self.abspath('DUMMY', '*')], unique=False)
        self.assert_same_command_record(records[0], dcrec1)
        self.assert_same_command_record(records[1], dcrec2)
        self.assertEqual(len(records), 2)

        records = self.search_command_record(
            cwd_glob=[self.abspath('REAL', '*')], unique=False)
        self.assertEqual(len(records), 0)

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
