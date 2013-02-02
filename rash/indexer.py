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
        if keep_json:
            check_duplicate = True
        self.conf = conf
        self.check_duplicate = check_duplicate
        self.keep_json = keep_json
        self.record_path = record_path or conf.record_path
        self.db = DataBase(conf.db_path)

    def index_record(self, json_path):
        """
        Import `json_path` and remove it if :attr:`keep_json` is false.
        """
        self.db.import_json(json_path, check_duplicate=self.check_duplicate)
        if not self.keep_json:
            os.remove(json_path)

    def index_all(self):
        """
        Index all records under :attr:`record_path`.
        """
        top_path = os.path.join(self.record_path, 'command')
        with self.db.connection():
            for (root, _, files) in os.walk(top_path):
                for f in (f for f in files if f.endswith('.json')):
                    self.index_record(os.path.join(root, f))
