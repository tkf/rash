import os
import sqlite3
from contextlib import closing

schema_version = '0.1.dev1'


class DataBase(object):

    schemapath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

    def __init__(self, dbpath):
        self.dbpath = dbpath
        if not os.path.exists(dbpath):
            self._init_db()

    def _get_db(self):
        """Returns a new connection to the database."""
        return closing(sqlite3.connect(self.dbpath))

    def _init_db(self):
        """Creates the database tables."""
        from .__init__ import __version__ as version
        with self._get_db() as db:
            with open(self.schemapath) as f:
                db.cursor().executescript(f.read())
            db.execute(
                'INSERT INTO rash_info (rash_version, schema_version) '
                'VALUES (?, ?)',
                [version, schema_version])
            db.commit()

    def import_json(self, json_path, **kwds):
        import json
        with open(json_path) as fp:
            self.import_dict(json.load(fp), **kwds)

    def import_dict(self, dct, check_duplicate=True):
        raise NotImplementedError
