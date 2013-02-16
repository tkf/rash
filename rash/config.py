"""
RASH configuration
==================

.. autoclass:: Configuration
   :members:
.. autoclass:: RecordConfig
   :members:
.. autoclass:: SearchConfig
   :members:
.. autoclass:: ISearchConfig
   :members:

"""

# FIXME: Remove ConfigStore then use ``autodoc_default_flags = ['members']``
# in ../doc/source/conf.py, so that I don't need to write `autoclass`
# explicitly like above.  To do so, add `get_config` function and another
# sub-configurable called PathConfig.

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

        self.daemon_log_level = 'INFO'  # FIXME: make this configurable
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

    If you define an object named :data:`config` in the
    :term:`configuration file`, it is going to be loaded by RASH.
    :data:`config` must be an instance of :class:`Configuration`.

    .. glossary::

       configuration file
         In unix-like systems, it's :file:`~/.config/rash/config.py` or
         different place if you set :envvar:`XDG_CONFIG_HOME`.  In Mac
         OS, it's :file:`~/Library/Application Support/RASH/config.py`.
         Use ``rash locate config`` to locate the exact place.

    Example:

    >>> from rash.config import Configuration
    >>> config = Configuration()
    >>> config.isearch.query = '-u .'

    Here is a list of configuration variables you can set:

    =========================== ===========================================
    Configuration variables
    =========================== ===========================================
    |record.environ|            Environment variables to record.
    |search.alias|              Search query alias.
    |search.kwds_adapter|       Transform keyword arguments.
    |isearch.query|             Default isearch query.
    |isearch.query_template|    Transform default query.
    |isearch.base_query|        Default isearch base query.
    =========================== ===========================================

    .. |record.environ| replace::
       :attr:`config.record.environ <RecordConfig.environ>`
    .. |search.alias| replace::
       :attr:`config.search.alias <SearchConfig.alias>`
    .. |search.kwds_adapter| replace::
       :attr:`config.search.kwds_adapter <SearchConfig.kwds_adapter>`
    .. |isearch.query| replace::
       :attr:`config.isearch.query <ISearchConfig.query>`
    .. |isearch.query_template| replace::
       :attr:`config.isearch.query_template <ISearchConfig.query_template>`
    .. |isearch.base_query| replace::
       :attr:`config.isearch.base_query <ISearchConfig.base_query>`

    """

    def __init__(self):
        self.record = RecordConfig()
        self.search = SearchConfig()
        self.isearch = ISearchConfig()


class RecordConfig(object):

    """
    Recording configuration.
    """

    def __init__(self):

        self.environ = {
            'init': [
                'SHELL', 'TERM', 'HOST', 'TTY', 'USER', 'DISPLAY',
                # SOMEDAY: Reevaluate if "RASH_SPENV_TERMINAL" is the
                # right choice.  Here, I am using `environ` dict as a
                # generic key value store.  Using 'RASH_SPENV_' as a
                # prefix key, it is very easy to add new variable to
                # track.
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
        >>> config.record.environ['command'] += ['VIRTUAL_ENV', 'PYTHONPATH']

        """


class SearchConfig(object):

    """
    Search configuration.
    """

    def __init__(self):

        self.alias = {}
        r"""
        Search query alias.

        It must be a dict-like object that maps a str to a list of str
        when "expanding" search query.

        Example:

        >>> config = Configuration()
        >>> config.search.alias['test'] = \
        ...     ["--exclude-pattern", "*rash *", "--include-pattern", "*test*"]

        then,::

            rash search test

        is equivalent to::

            rash search --exclude-pattern "*rash *" --include-pattern "*test*"

        """

        self.kwds_adapter = lambda x: x
        """
        A function to transform keyword arguments.

        This function takes a dictionary from command line argument
        parser and can modify the dictionary to do whatever you want
        to do with it.  It is much more lower-level and powerful than
        :attr:`alias`.  This function must return the modified,
        or possibly new dictionary.

        Example definition that does the same effect as the example in
        :attr:`alias`:

        >>> def adapter(kwds):
        ...     if 'test' in kwds.get('pattern', []):
        ...         kwds['pattern'] = [p for p in kwds['pattern']
        ...                            if p != 'test']
        ...         kwds['exclude_pattern'].append("*rash *")
        ...         kwds['include_pattern'].append("*test*")
        ...     return kwds
        ...
        >>> config = Configuration()
        >>> config.search.kwds_adapter = adapter

        """


class ISearchConfig(object):

    """
    Configure how ``rash isearch`` is started.

    See also :class:`SearchConfig`.  Once isearch UI is started,
    :class:`SearchConfig` controls how search query is interpreted.
    For example, aliases defined in :class:`SearchConfig` can be used
    in isearch.

    """

    def __init__(self):

        self.query = ''
        """
        Set default value (str) for ``--query`` option.

        If you want to start isearch with the query ``-d .`` (only
        list the command executed at this directory), use the
        following configuration:

        >>> config = Configuration()
        >>> config.isearch.query = '-d . '

        As ``rash-zle-isearch`` passes the current line content to
        ``--query`` which override this setting, you need to use
        :attr:`query_template` instead if you want to configure the
        default query.

        """

        self.query_template = '{0}'
        """
        Transform default query using Python string format.

        The string format should have only one field ``{0}``.
        The query given by ``-query`` or the one specified by
        :attr:`query` fills that filed.  Default value is
        do-nothing template ``'{0}'``.

        >>> config = Configuration()
        >>> config.isearch.query_template = '-d . {0}'

        """

        self.base_query = []
        """
        Set default value (list of str) for ``--base-query`` option.
        """
