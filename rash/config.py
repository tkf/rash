import os

from .utils.confutils import get_config_directory
from .utils.pathutils import mkdirp


class ConfigStore(object):

    """
    Configuration and data file store.

    RASH stores data in the following directory in Linux::

      * ~/.config/               # $XDG_CONFIG_HOME
      `--* rash/                 # base_path
         |--* daemon.pid         # PID of daemon process
         |--* daemon.log         # Log file for daemon
         `--* data/              # data_path
            |--* db.sqlite       # db_path ("indexed" record)
            `--* record/         # record_path ("raw" record)
               |--* command/     # command log
               `--* init/        # initialization log

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

    daemon_pid_path = os.path.join(base_path, 'daemon.pid')
    """
    A file to store daemon PID (``~/.config/rash/daemon.pid``).
    """

    daemon_log_path = os.path.join(base_path, 'daemon.log')
    """
    Daemon log file (``~/.config/rash/daemon.log``).
    """

    daemon_log_level = 'INFO'
    """
    Daemon log level.
    """

    def __init__(self):
        mkdirp(self.record_path)
