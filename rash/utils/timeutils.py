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
