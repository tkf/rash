# Copyright (C) 2013-  Takafumi Arakaki

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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

        self.config_path = os.path.join(self.base_path, 'config.py')
        """
        File to store user configuration (``~/.config/rash/config.py``).
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

    def get_config(self):
        """
        Load user configuration or return default when not found.

        :rtype: :class:`Configuration`

        """
        if not self._config:
            namespace = {}
            if os.path.exists(self.config_path):
                execfile(self.config_path, namespace)
            self._config = namespace.get('config') or Configuration()
        return self._config
    _config = None


class Configuration(object):

    """
    RASH configuration interface.

    If you define an object named `config` in ``~/.config/rash/config.py``,
    it is going to be loaded by RASH.

    Example::

        from rash.config import Configuration
        config = Configuration()
        config.isearch_query = '-u .'

    """

    def __init__(self):

        self.record_environ = {
            'init': [
                'SHELL', 'TERM', 'HOST', 'TTY', 'USER', 'DISPLAY',
                'RASH_SPENV_TERMINAL',
            ],
            'exit': [],
            'command': ['PATH'],
        }
        """
        Environment variables to record.

        Each key (str) represent record type (init/exit/command).
        Each value (list of str) is a list of environment variables to
        record.

        Example usage:

        >>> config = Configuration()
        >>> config.record_environ['init'] += ['VIRTUAL_ENV', 'PYTHONPATH']

        """

        self.search_pattern_expander = lambda _: None
        """
        Search query expander.

        It must be a callable object that returns a list of string when
        "expanding" search query.  Returning None means to use the query
        as-is.

        Example::

        >>> def pattern_expander(query):
        ...     if query == 'test':
        ...         return ["--exclude-pattern", "*rash *",
        ...                 "--include-pattern", "*test*"]
        >>> config = Configuration()
        >>> config.search_pattern_expander = pattern_expander

        then,::

            rash search test

        is equivalent to::

            rash search --exclude-pattern "*rash *" --include-pattern "*test*"

        """

        self.isearch_query = ''
        """
        Set default value (str) for "isearch --query".
        """

        self.isearch_base_query = []
        """
        Set default value (list of str) for "isearch --base-query".
        """
