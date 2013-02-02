import os

from .utils.confutils import get_config_directory
from .utils.pathutils import mkdirp


class ConfigStore(object):

    """
    Configuration and data file store.

    RASH stores data in the following directory in Linux::

      * ~/.config/               # $XDG_CONFIG_HOME
      `--* rash/                 # base_path
         `--* data/              # data_path
            |--* db.sqlite       # db_path
            `--* record/         # record_path

    In Mac OS and Windows, :attr:`base_path` may be different but
    structure in the directory is the same.

    """

    base_path = get_config_directory('RASH')
    """
    Root directory for any RASH related data files (``~/.config/rash``).
    """

    data_path = os.path.join(base_path, 'data')
    """
    Directory to store data collected by RASH (``~/.config/rash/data``).
    """

    record_path = os.path.join(data_path, 'record')
    """
    Shell history is stored in this directory at the first stage.

    In Linux: ``~/.config/rash/data/record/``.

    """

    db_path = os.path.join(data_path, 'db.sqlite')
    """
    Shell history is stored in the DB at this path before it is search-able.

    In Linux: ``~/.config/rash/data/db.sqlite``.

    """

    def __init__(self):
        mkdirp(self.record_path)
