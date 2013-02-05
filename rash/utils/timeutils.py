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
