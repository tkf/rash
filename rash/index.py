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


def index_run(record_path, keep_json, check_duplicate):
    """
    Convert raw JSON records into sqlite3 DB.

    Normally RASH launches a daemon that takes care of indexing.
    See ``rash daemon --help``.

    """
    from .config import ConfigStore
    from .indexer import Indexer
    cfstore = ConfigStore()
    indexer = Indexer(cfstore, check_duplicate, keep_json, record_path)
    indexer.index_all()


def index_add_arguments(parser):
    parser.add_argument(
        'record_path', nargs='?',
        help="""
        specify the directory that has JSON records.
        """)
    parser.add_argument(
        '--keep-json', default=False, action='store_true',
        help="""
        Do not remove old JSON files.  It turns on --check-duplicate.
        """)
    parser.add_argument(
        '--check-duplicate', default=False, action='store_true',
        help='do not store already existing history in DB.')


commands = [
    ('index', index_add_arguments, index_run),
]
