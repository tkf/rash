import time
import datetime
from parsedatetime import parsedatetime


def parse_datetime(string):
    cal = parsedatetime.Calendar()
    dates = cal.parse(string)
    if dates:
        return datetime.datetime.utcfromtimestamp(time.mktime(dates[0]))
