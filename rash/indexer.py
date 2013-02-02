import os

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
                'At this point, --keep-json should be specified.')
        if keep_json:
            check_duplicate = True
        self.conf = conf
        self.check_duplicate = check_duplicate
        self.keep_json = keep_json
        self.record_path = record_path or conf.record_path
        self.db = DataBase(conf.db_path)
        if record_path:
            self.check_path(record_path, '`record_path`')

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
        if self.get_record_type(json_path) != 'command':
            # FIXME: Implement index_record for other record types!
            return
        self.db.import_json(json_path, check_duplicate=self.check_duplicate)
        if not self.keep_json:
            self.logger.info('Removing JSON record: %s', json_path)
            os.remove(json_path)

    def index_all(self):
        """
        Index all records under :attr:`record_path`.
        """
        self.logger.debug('Start indexing all records under: %s',
                          self.record_path)
        with self.db.connection():
            for (root, _, files) in os.walk(self.record_path):
                for f in (f for f in files if f.endswith('.json')):
                    self.index_record(os.path.join(root, f))
