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


def show_run(command_history_id):
    """
    Show detailed command history by its ID.
    """
    from pprint import pprint
    from .config import ConfigStore
    from .database import DataBase
    db = DataBase(ConfigStore().db_path)
    with db.connection():
        for ch_id in command_history_id:
            crec = db.get_full_command_record(ch_id)
            pprint(crec.__dict__)
            print("")


def show_add_arguments(parser):
    parser.add_argument(
        'command_history_id', nargs='+', type=int,
        help="""
        Integer ID of command history.
        """)


commands = [
    ('show', show_add_arguments, show_run),
]
