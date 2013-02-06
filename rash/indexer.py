import os
import json
import warnings

from .database import DataBase


class Indexer(object):

    """
    Translate JSON files into SQLite DB.
    """

    def __init__(self, conf, check_duplicate, keep_json, record_path=None):
        """
        Create an indexer.

        :type            conf: rash.config.ConfigStore
        :arg             conf:
        :type check_duplicate: bool
        :arg  check_duplicate: See :meth:`DataBase.import_dict`.
        :type       keep_json: bool
        :arg        keep_json: Do not remove JSON files.
                               Imply ``check_duplicate=True``.
        :type     record_path: str or None
        :arg      record_path: Default to `conf.record_path`.

        """
        from .log import logger
        self.logger = logger
        if not keep_json:
            raise RuntimeError(
                'At this point, --keep-json should be specified.')  # FIXME
        if keep_json:
            check_duplicate = True
        self.conf = conf
        self.check_duplicate = check_duplicate
        self.keep_json = keep_json
        self.record_path = record_path or conf.record_path
        self.db = DataBase(conf.db_path)
        if record_path:
            self.check_path(record_path, '`record_path`')

        self.logger.debug('Indexer initialized')
        self.logger.debug('check_duplicate = %r', self.check_duplicate)
        self.logger.debug('keep_json = %r', self.keep_json)
        self.logger.debug('record_path = %r', self.record_path)

    def get_record_type(self, path):
        relpath = os.path.relpath(path, self.conf.record_path)
        dirs = relpath.split(os.path.sep, 1)
        return dirs[0] if dirs else None

    def check_path(self, path, name='path'):
        if self.get_record_type(path) not in ['command', 'init', 'exit']:
            raise RuntimeError(
                '{0} must be under {1}'.format(
                    name,
                    os.path.join(self.conf.record_path,
                                 '{command,init,exit}',
                                 '')))

    def index_record(self, json_path):
        """
        Import `json_path` and remove it if :attr:`keep_json` is false.
        """
        self.logger.debug('Indexing record: %s', json_path)
        json_path = os.path.abspath(json_path)
        self.check_path(json_path, '`json_path`')

        with open(json_path) as fp:
            try:
                dct = json.load(fp)
            except ValueError:
                warnings.warn(
                    'Ignoring invalid JSON file at: {0}'.format(json_path))
                return

        record_type = self.get_record_type(json_path)
        kwds = {}
        if record_type == 'command':
            importer = self.db.import_dict
            kwds.update(check_duplicate=self.check_duplicate)
        elif record_type == 'init':
            importer = self.db.import_init_dict
        elif record_type == 'exit':
            importer = self.db.import_exit_dict
        else:
            raise ValueError("Unknown record type: {0}".format(record_type))
        importer(dct, **kwds)

        if not self.keep_json:
            self.logger.info('Removing JSON record: %s', json_path)
            os.remove(json_path)

    def find_record_files(self):
        """
        Yield paths to record files.
        """
        for (root, _, files) in os.walk(self.record_path):
            for f in (f for f in files if f.endswith('.json')):
                yield os.path.join(root, f)

    def index_all(self):
        """
        Index all records under :attr:`record_path`.
        """
        self.logger.debug('Start indexing all records under: %s',
                          self.record_path)
        with self.db.connection():
            for json_path in sorted(self.find_record_files()):
                self.index_record(json_path)
