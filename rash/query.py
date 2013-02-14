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

from argparse import ArgumentParser

from .search import SORT_KEY_SYNONYMS


class SafeArgumentParser(ArgumentParser):

    def exit(self, *_, **__):
        raise ValueError

    def print_usage(self, *_):
        pass

    print_help = print_version = print_usage


def preprocess_kwds(kwds):
    """
    Preprocess keyword arguments for `DataBase.search_command_record`.
    """
    from .utils.timeutils import parse_datetime, parse_duration

    for key in ['output', 'format', 'with_command_id', 'with_session_id']:
        kwds.pop(key, None)

    for key in ['time_after', 'time_before']:
        val = kwds[key]
        if val:
            dt = parse_datetime(val)
            if dt:
                kwds[key] = dt

    for key in ['duration_longer_than', 'duration_less_than']:
        val = kwds[key]
        if val:
            dt = parse_duration(val)
            if dt:
                kwds[key] = dt

    # interpret "pattern" (currently just copying to --include-pattern)
    less_strict_pattern = list(map("*{0}*".format, kwds.pop('pattern', [])))
    kwds['match_pattern'] = kwds['match_pattern'] + less_strict_pattern

    kwds['sort_by'] = SORT_KEY_SYNONYMS[kwds['sort_by']]
    return kwds
