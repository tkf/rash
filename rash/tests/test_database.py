import os
import datetime

from ..model import CommandRecord
from ..database import DataBase, normalize_directory
from .utils import BaseTestCase


def setdefaults(d, **kwds):
    for (k, v) in kwds.items():
        d.setdefault(k, v)


def to_sql_timestamp(ts):
    if ts is not None:
        dt = datetime.datetime.utcfromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def to_command_record(data):
    crec = CommandRecord(**data)
    crec.cwd = normalize_directory(crec.cwd)
    crec.start = to_sql_timestamp(crec.start)
    crec.stop = to_sql_timestamp(crec.stop)
    return crec


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
        return self.db.search_command_record(**kwds)

    def assert_same_command_record(
            self, crec1, crec2,
            keys=['command', 'cwd', 'terminal', 'start', 'stop', 'exit_code']):
        asdict = lambda rec: dict((k, getattr(rec, k)) for k in keys)
        self.assertEqual(asdict(crec1), asdict(crec2))

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

    def test_import_command_record(self):
        data = self.get_dummy_command_record_data()
        self.db.import_dict(data)
        records = list(self.search_command_record())
        crec = records[0]
        self.assert_same_command_record(crec, to_command_record(data))
        self.assertEqual(len(records), 1)

    def test_import_command_record_no_check_duplicate(self):
        data = self.get_dummy_command_record_data()
        num = 3
        for _ in range(num):
            self.db.import_dict(data, check_duplicate=False)
        records = list(self.search_command_record(unique=False))
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
        records = list(self.search_command_record(unique=False))
        self.assert_same_command_record(records[0], to_command_record(data))
        self.assertEqual(len(records), 1)
