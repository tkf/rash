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

    def __init__(self, base_path=None):
        self.base_path = base_path or get_config_directory('RASH')
        """
        Root directory for any RASH related data files (``~/.config/rash``).
        """

        self.data_path = os.path.join(self.base_path, 'data')
        """
        Directory to store data collected by RASH (``~/.config/rash/data``).
        """

        self.record_path = os.path.join(self.data_path, 'record')
        """
        Shell history is stored in this directory at the first stage.
        """

        self.db_path = os.path.join(self.data_path, 'db.sqlite')
        """
        Shell history is stored in the DB at this path.
        """

        self.daemon_pid_path = os.path.join(self.base_path, 'daemon.pid')
        """
        A file to store daemon PID (``~/.config/rash/daemon.pid``).
        """

        self.daemon_log_path = os.path.join(self.base_path, 'daemon.log')
        """
        Daemon log file (``~/.config/rash/daemon.log``).
        """

        self.daemon_log_level = 'INFO'
        """
        Daemon log level.
        """

        mkdirp(self.record_path)
