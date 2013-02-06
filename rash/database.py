import os
import sqlite3
from contextlib import closing, contextmanager
import datetime
import warnings
import itertools

from .utils.iterutils import nonempty, repeat
from .model import CommandRecord, SessionRecord

schema_version = '0.1.dev1'


def concat_expr(operator, conditions):
    """
    Concatenate `conditions` with `operator` and wrap it by ().

    It returns a string in a list or empty list, if `conditions` is empty.

    """
    expr = " {0} ".format(operator).join(conditions)
    return ["({0})".format(expr)] if expr else []


def convert_ts(ts):
    """
    Convert timestamp (ts)

    :type ts: int or str or None
    :arg  ts: Unix timestamp
    :rtype: datetime.datetime or str or None

    """
    if ts is None:
        return None
    try:
        return datetime.datetime.utcfromtimestamp(ts)
    except TypeError:
        pass
    return ts


def normalize_directory(path):
    """
    Append "/" to `path` if needed.
    """
    if path is None:
        return None
    if path.endswith(os.path.sep):
        return path
    else:
        return path + os.path.sep


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
            # FIXME: Make rash_info table to automatically update when
            # the versions are changed.
            db.execute(
                'INSERT INTO rash_info (rash_version, schema_version) '
                'VALUES (?, ?)',
                [version, schema_version])
            db.commit()

    @contextmanager
    def connection(self, commit=False):
        """
        Context manager to keep around DB connection.

        :rtype: sqlite3.Connection

        SOMEDAY: Get rid of this function.  Keeping connection around as
        an argument to the method using this context manager is
        probably better as it is more explicit.

        """
        if commit:
            self._need_commit = True
        if self._db:
            yield self._db
        else:
            try:
                with self._get_db() as db:
                    self._db = db
                    yield self._db
                    if self._need_commit:
                        db.commit()
            finally:
                self._db = None
                self._need_commit = False
    _db = None
    _need_commit = False

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
        with self.connection(commit=True) as connection:
            db = connection.cursor()
            ch_id = self._insert_command_history(db, crec)
            self._isnert_command_environment(db, ch_id, crec.environ)
            self._insert_pipe_status(db, ch_id, crec.pipestatus)

    def _insert_command_history(self, db, crec):
        command_id = self._get_maybe_new_command_id(db, crec.command)
        session_id = self._get_maybe_new_session_id(db, crec.session_id)
        directory_id = self._get_maybe_new_directory_id(db, crec.cwd)
        terminal_id = self._get_maybe_new_terminal_id(db, crec.terminal)
        db.execute(
            '''
            INSERT INTO command_history
                (command_id, session_id, directory_id, terminal_id,
                 start_time, stop_time, exit_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            [command_id, session_id, directory_id, terminal_id,
             convert_ts(crec.start), convert_ts(crec.stop), crec.exit_code])
        return db.lastrowid

    def _isnert_command_environment(self, db, ch_id, environ):
        self._insert_environ(db, 'command_environment_map', 'ch_id', ch_id,
                             environ)

    def _insert_environ(self, db, table, id_name, ch_id, environ):
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
                INSERT INTO {0}
                    ({1}, ev_id)
                VALUES (?, ?)
                '''.format(table, id_name),
                [ch_id, ev_id])

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

    def _get_maybe_new_session_id(self, db, session_long_id):
        if session_long_id is None:
            return None
        return self._get_maybe_new_id(
            db, 'session_history', {'session_long_id': session_long_id})

    def _get_maybe_new_directory_id(self, db, directory):
        if directory is None:
            return None
        directory = normalize_directory(directory)
        return self._get_maybe_new_id(
            db, 'directory_list', {'directory': directory})

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
        """
        Yield records that matches to `crec`.

        All attributes of `crec` except for `environ` are concerned.

        """
        keys = ['command_history_id', 'command', 'session_history_id',
                'cwd', 'terminal',
                'start', 'stop', 'exit_code']
        sql = """
        SELECT
            command_history.id, CL.command, session_id,
            DL.directory, TL.terminal,
            start_time, stop_time, exit_code
        FROM command_history
        LEFT JOIN command_list AS CL ON command_id = CL.id
        LEFT JOIN directory_list AS DL ON directory_id = DL.id
        LEFT JOIN terminal_list AS TL ON terminal_id = TL.id
        WHERE
            (CL.command   = ? OR (CL.command   IS NULL AND ? IS NULL)) AND
            (DL.directory = ? OR (DL.directory IS NULL AND ? IS NULL)) AND
            (TL.terminal  = ? OR (TL.terminal  IS NULL AND ? IS NULL)) AND
            (start_time   = ? OR (start_time   IS NULL AND ? IS NULL)) AND
            (stop_time    = ? OR (stop_time    IS NULL AND ? IS NULL)) AND
            (exit_code    = ? OR (exit_code    IS NULL AND ? IS NULL))
        """
        desired_row = [
            crec.command, normalize_directory(crec.cwd), crec.terminal,
            convert_ts(crec.start), convert_ts(crec.stop), crec.exit_code]
        params = list(itertools.chain(*zip(desired_row, desired_row)))
        with self.connection() as connection:
            for row in connection.execute(sql, params):
                yield CommandRecord(**dict(zip(keys, row)))

    def search_command_record(self, **kwds):
        """
        Search command history.

        :rtype: [CommandRecord]

        """
        (sql, params, keys) = self._compile_sql_search_command_record(**kwds)
        with self.connection() as connection:
            cur = connection.cursor()
            for row in cur.execute(sql, params):
                yield CommandRecord(**dict(zip(keys, row)))

    def _compile_sql_search_command_record(
            cls, limit, pattern, cwd, cwd_glob, cwd_under, unique,
            time_after, time_before, duration_longer_than, duration_less_than,
            include_exit_code, exclude_exit_code,
            session_history_id=None,
            **_):
        keys = ['command_history_id', 'command', 'session_history_id',
                'cwd', 'terminal',
                'start', 'stop', 'exit_code']
        columns = ['command_history.id', 'CL.command', 'session_id',
                   'DL.directory', 'TL.terminal',
                   'start_time', 'stop_time', 'exit_code']
        max_index = 5
        assert columns[max_index] == 'start_time'
        params = []
        conditions = []

        if cwd_under:
            cwd_glob.extend(os.path.join(os.path.abspath(p), "*")
                            for p in cwd_under)

        def add_or_match(template, name, args):
            conditions.extend(concat_expr(
                'OR', repeat(template.format(name), len(args))))
            params.extend(args)

        add_or_match('glob(?, {0})', 'CL.command', pattern)
        add_or_match('glob(?, {0})', 'DL.directory', cwd_glob)
        add_or_match('{0} = ?', 'DL.directory',
                     [normalize_directory(os.path.abspath(p)) for p in cwd])

        if time_after:
            conditions.append('DATETIME(start_time) >= ?')
            params.append(time_after)

        if time_before:
            conditions.append('DATETIME(start_time) <= ?')
            params.append(time_before)

        command_duration = (
            '(JULIANDAY(stop_time) - JULIANDAY(start_time)) * 60 * 60 * 24')

        if duration_longer_than:
            conditions.append('({0} >= ?)'.format(command_duration))
            params.append(duration_longer_than)

        if duration_less_than:
            conditions.append('({0} <= ?)'.format(command_duration))
            params.append(duration_less_than)

        add_or_match('{0} = ?', 'exit_code', include_exit_code)
        conditions.extend(repeat('exit_code != ?', len(exclude_exit_code)))
        params.extend(exclude_exit_code)

        if session_history_id:
            conditions.append('(session_id = ?)')
            params.append(session_history_id)

        where = ''
        if conditions:
            where = 'WHERE {0} '.format(" AND ".join(conditions))

        group_by = ''
        if unique:
            columns[max_index] = 'MAX({0})'.format(columns[max_index])
            group_by = 'GROUP BY CL.command '

        sql_limit = ''
        if limit and limit >= 0:
            sql_limit = 'LIMIT ?'
            params.append(limit)

        sql = (
            'SELECT {columns} '
            'FROM command_history '
            'LEFT JOIN command_list AS CL ON command_id = CL.id '
            'LEFT JOIN directory_list AS DL ON directory_id = DL.id '
            'LEFT JOIN terminal_list AS TL ON terminal_id = TL.id '
            '{where}{group_by} '
            'ORDER BY start_time '
            '{limit}'
        ).format(
            columns=', '.join(columns),
            where=where,
            group_by=group_by,
            limit=sql_limit,
        )
        return (sql, params, keys)

    def import_init_dict(self, dct, overwrite=True):
        long_id = dct['session_id']
        srec = SessionRecord(**dct)
        with self.connection(commit=True) as connection:
            db = connection.cursor()
            records = list(self.select_session_by_long_id(long_id))
            if records:
                assert len(records) == 1
                oldrec = records[0]
                if oldrec.start is not None and not overwrite:
                    return
                oldrec.start = srec.start
                sh_id = self._update_session_history(db, oldrec)
            else:
                sh_id = self._insert_session_history(db, srec)
            self._update_session_environ(db, sh_id, srec.environ)

    def import_exit_dict(self, dct, overwrite=True):
        long_id = dct['session_id']
        srec = SessionRecord(**dct)
        with self.connection(commit=True) as connection:
            db = connection.cursor()
            records = list(self.select_session_by_long_id(long_id))
            if records:
                assert len(records) == 1
                oldrec = records[0]
                if oldrec.stop is not None and not overwrite:
                    return
                oldrec.stop = srec.stop
                self._update_session_history(db, oldrec)
            else:
                self._insert_session_history(db, srec)

    def _insert_session_history(self, db, srec):
        db.execute(
            '''
            INSERT INTO session_history
                (session_long_id, start_time, stop_time)
            VALUES (?, ?, ?)
            ''',
            [srec.session_id, convert_ts(srec.start), convert_ts(srec.stop)])
        return db.lastrowid

    def _update_session_history(self, db, srec):
        assert srec.session_history_id is not None
        db.execute(
            '''
            UPDATE session_history
            SET session_long_id=?, start_time=?, stop_time=?
            WHERE id=?
            ''',
            [srec.session_id, convert_ts(srec.start), convert_ts(srec.stop),
             srec.session_history_id])
        return srec.session_history_id

    def _update_session_environ(self, db, sh_id, environ):
        if not environ:
            return
        db.execute('DELETE FROM session_environment_map WHERE sh_id=?',
                   [sh_id])
        self._insert_session_environ(db, sh_id, environ)

    def _insert_session_environ(self, db, sh_id, environ):
        self._insert_environ(db, 'session_environment_map', 'sh_id', sh_id,
                             environ)

    def select_session_by_long_id(self, long_id):
        keys = ['session_history_id', 'session_id', 'start', 'stop']
        sql = """
        SELECT id, session_long_id, start_time, stop_time
        FROM session_history
        WHERE session_long_id = ?
        """
        params = [long_id]
        with self.connection() as connection:
            for row in connection.execute(sql, params):
                yield SessionRecord(**dict(zip(keys, row)))

    def search_session_record(self, session_id):
        return self.select_session_by_long_id(session_id)

    def get_full_command_record(self, command_history_id,
                                merge_session_environ=True):
        """
        Get fully retrieved :class:`CommandRecord` instance by ID.

        By "fully", it means that complex slots such as `environ` and
        `pipestatus` are available.

        :type    command_history_id: int
        :type merge_session_environ: bool

        """
        with self.connection() as db:
            crec = self._select_command_record(db, command_history_id)
            crec.pipestatus = self._get_pipestatus(db, command_history_id)
            # Set environment variables
            cenv = self._select_environ(db, 'command', command_history_id)
            crec.environ.update(cenv)
            if merge_session_environ:
                senv = self._select_environ(
                    db, 'session', crec.session_history_id)
                crec.environ.update(senv)
        return crec

    def _select_command_record(self, db, command_history_id):
        keys = ['session_history_id', 'command', 'cwd', 'terminal',
                'start', 'stop', 'exit_code']
        sql = """
        SELECT
            session_id, CL.command, DL.directory, TL.terminal,
            start_time, stop_time, exit_code
        FROM command_history
        LEFT JOIN command_list AS CL ON command_id = CL.id
        LEFT JOIN directory_list AS DL ON directory_id = DL.id
        LEFT JOIN terminal_list AS TL ON terminal_id = TL.id
        WHERE command_history.id = ?
        """
        params = [command_history_id]
        for row in db.execute(sql, params):
            crec = CommandRecord(**dict(zip(keys, row)))
            crec.command_history_id = command_history_id
            return crec
        raise ValueError("Command record of id={0} is not found"
                         .format(command_history_id))

    def _get_pipestatus(self, db, command_history_id):
        sql = """
        SELECT program_position, exit_code
        FROM pipe_status_map
        WHERE ch_id = ?
        """
        params = [command_history_id]
        records = list(db.execute(sql, params))
        length = max(r[0] for r in records) + 1
        pipestatus = [None] * length
        for (i, s) in records:
            pipestatus[i] = s
        return pipestatus

    def _select_environ(self, db, recname, recid):
        sql = """
        SELECT
            EVar.variable_name, EVar.variable_value
        FROM {recname}_environment_map as EMap
        LEFT JOIN environment_variable AS EVar ON EMap.ev_id = EVar.id
        WHERE EMap.{hist_id} = ?
        """.format(
            recname=recname,
            hist_id='ch_id' if recname == 'command' else 'sh_id',
        )
        params = [recid]
        return db.execute(sql, params)
