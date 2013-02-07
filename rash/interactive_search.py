import re
import shlex

try:
    from percol.finder import FinderMultiQueryString
    assert FinderMultiQueryString  # fool pyflakes
except ImportError:
    # Dummy class for making this module importable:
    FinderMultiQueryString = object

from argparse import ArgumentParser
from .search import search_add_arguments, preprocess_kwds


def strip_glob(string, split_str=' '):
    """
    Strip glob portion in `string`.

    >>> strip_glob('*glob*like')
    'glob like'
    >>> strip_glob('glob?')
    'glo'
    >>> strip_glob('glob[seq]')
    'glob'
    >>> strip_glob('glob[!seq]')
    'glob'

    :type string: str
    :rtype: str

    """
    string = _GLOB_PORTION_RE.sub(split_str, string)
    return string.strip()

_GLOB_PORTION_RE = re.compile(r'\*|.\?|\[[^\]]+\]')


class SafeArgumentParser(ArgumentParser):

    def exit(self, *_, **__):
        raise ValueError

    def print_usage(self, *_):
        pass

    print_help = print_version = print_usage


class RashFinder(FinderMultiQueryString):

    def __init__(self, *args, **kwds):
        super(RashFinder, self).__init__(*args, **kwds)

        self.__parser = parser = SafeArgumentParser()
        search_add_arguments(parser)

    # Generator should be terminated in order to close connection to
    # sqlite.  Otherwise, sqlite3 modules raise an error saying that
    # it doesn't support multi-threading access.
    lazy_finding = False

    def find(self, query, collection=None):
        try:
            # shlex < 2.7.3 does not work with unicode:
            args = shlex.split(query.encode())
            kwds = preprocess_kwds(vars(self.__parser.parse_args(args)))
        except (ValueError, SyntaxError):
            return super(RashFinder, self).find(query, collection)

        # SOMEDAY: get rid of this hard-coded search limit by making
        # `search_command_record` thread-safe and setting
        # `lazy_finding = True`.
        kwds['limit'] = 50 if kwds['pattern'] else 1000

        # Strict glob search is a little bit cumbersome in interactive
        # search.  So, make the match a bit more permissive.
        kwds['pattern'] = list(map("*{0}*".format, kwds['pattern']))

        records = self.db.search_command_record(**kwds)
        self.collection = collection = (r.command for r in records)

        return super(RashFinder, self).find(
            self.split_str.join(strip_glob(q, self.split_str)
                                for q in kwds['pattern']),
            collection)


def load_rc(percol, path=None, encoding=None):
    import os
    from percol import debug
    if path is None:
        path = os.path.expanduser("~/.percol.d/rc.py")
    try:
        with open(path, 'r') as rc:
            exec(rc.read().decode(encoding or 'utf-8'), locals())
    except Exception as e:
        debug.log("exception", e)


def launch_isearch(conf, rcfile=None, input_encoding=None, **kwds):
    from percol import Percol
    from percol import tty
    import percol.actions as actions

    from .database import DataBase

    # Pass db instance to finder.  Not clean but works and no harm.
    RashFinder.db = DataBase(conf.db_path)

    ttyname = tty.get_ttyname()
    with open(ttyname, "r+w") as tty_f:
        with Percol(descriptors=tty.reconnect_descriptors(tty_f),
                    finder=RashFinder,
                    actions=(actions.output_to_stdout,),
                    **kwds) as percol:
            load_rc(percol, rcfile, input_encoding)
            exit_code = percol.loop()

    exit(exit_code)
