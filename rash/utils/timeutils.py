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


import time
import datetime

try:
    from parsedatetime import parsedatetime
    HAS_PARSEDATETIME = True
except:
    HAS_PARSEDATETIME = False


def parse_datetime(string):
    if not HAS_PARSEDATETIME:
        return
    cal = parsedatetime.Calendar()
    dates = cal.parse(string)
    if dates:
        return datetime.datetime.utcfromtimestamp(time.mktime(dates[0]))


def parse_duration(string):
    """
    Parse human readable duration.

    >>> parse_duration('1m')
    60
    >>> parse_duration('7 days') == 7 * 24 * 60 * 60
    True

    """
    if string.isdigit():
        return int(string)
    try:
        return float(string)
    except ValueError:
        pass
    string = string.rstrip()
    for (suf, mult) in DURATION_SUFFIX_MAP.items():
        if string.lower().endswith(suf):
            try:
                return parse_duration(string[:-len(suf)].strip()) * mult
            except TypeError:
                return


DURATION_SUFFIX_MAP = {
    'minute': 60,
    'hour': 60 * 60,
    'day': 60 * 60 * 24,
}


def _add_duration():
    dsm = DURATION_SUFFIX_MAP
    additional = {}
    for (suf, mult) in dsm.items():
        additional[suf[0]] = mult
        additional[suf + 's'] = mult
    dsm['min'] = dsm['minute']
    dsm.update(additional)

_add_duration()
