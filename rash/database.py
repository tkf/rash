import os
import sqlite3
from contextlib import closing, contextmanager
import warnings

from .utils.iterutils import nonempty
from .model import CommandRecord

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
            try:
                dct = json.load(fp)
            except ValueError:
                warnings.warn(
                    'Ignoring invalid JSON file at: {0}'.format(json_path))
                return
        self.import_dict(dct, **kwds)

    def import_dict(self, dct, check_duplicate=True):
        crec = CommandRecord(**dct)
        if check_duplicate and nonempty(self.select_by_command_record(crec)):
            return
        with self._get_db() as connection:
            db = connection.cursor()
            ch_id = self._insert_command_history(db, crec)
            self._insert_environ(db, ch_id, crec.environ)
            self._insert_cwd(db, ch_id, crec.cwd)
            self._insert_pipe_status(db, ch_id, crec.pipestatus)
            connection.commit()

    def _insert_command_history(self, db, crec):
        command_id = self._get_maybe_new_command_id(db, crec.command)
        terminal_id = self._get_maybe_new_terminal_id(db, crec.terminal)
        db.execute(
            '''
            INSERT INTO command_history
                (command_id, start_time, stop_time, exit_code,
                 terminal_id)
            VALUES (?, ?, ?, ?, ?)
            ''',
            [command_id, crec.start, crec.stop, crec.exit_code,
             terminal_id])
        return db.lastrowid

    def _insert_environ(self, db, ch_id, environ):
        if not environ:
            return
        for (name, value) in environ.items():
            if name is None or value is None:
                continue
            ev_id = self._get_maybe_new_id(
                db, 'environment_variable',
                {'variable_name': name, 'variable_value': value})
            db.execute(
                '''
                INSERT INTO command_environment_map
                    (ch_id, ev_id)
                VALUES (?, ?)
                ''',
                [ch_id, ev_id])

    def _insert_cwd(self, db, ch_id, cwd):
        if not cwd:
            return
        dir_id = self._get_maybe_new_id(
            db, 'directory_list', {'directory': cwd})
        db.execute(
            'INSERT INTO command_cwd_map (ch_id, dir_id) VALUES (?, ?)',
            [ch_id, dir_id])

    def _insert_pipe_status(self, db, ch_id, pipe_status):
        if not pipe_status:
            return
        for (i, code) in enumerate(pipe_status):
            db.execute(
                '''
                INSERT INTO pipe_status_map
                    (ch_id, program_position, exit_code)
                VALUES (?, ?, ?)
                ''',
                [ch_id, i, code])

    def _get_maybe_new_command_id(self, db, command):
        if command is None:
            return None
        return self._get_maybe_new_id(
            db, 'command_list', {'command': command})

    def _get_maybe_new_terminal_id(self, db, terminal):
        if terminal is None:
            return None
        return self._get_maybe_new_id(
            db, 'terminal_list', {'terminal': terminal})

    def _get_maybe_new_id(self, db, table, columns):
        kvlist = list(columns.items())
        values = [v for (_, v) in kvlist]
        sql_select = 'SELECT id FROM "{0}" WHERE {1}'.format(
            table,
            ' AND '.join(map('"{0[0]}" = ?'.format, kvlist)),
        )
        for (id_val,) in db.execute(sql_select, values):
            return id_val
        sql_insert = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(
            table,
            ', '.join(map('"{0[0]}"'.format, kvlist)),
            ', '.join('?' for _ in kvlist),
        )
        db.execute(sql_insert, values)
        return db.lastrowid

    def select_by_command_record(self, crec):
        return []
        raise NotImplementedError