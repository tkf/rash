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


def isearch_run(**kwds):
    r"""
    Interactive history search that updated as you type.

    The query for this program is the same as the one for
    ``rash search`` command.

    You need percol_ to use this command.

    _percol: https://github.com/mooz/percol

    If you use zsh, you can setup a keybind like this to quickly
    launch iserch and execute the result.::

      # Type `Ctrl-x r` to start isearch
      bindkey "^Xr" rash-zle-isearch

    If you like command or you are not using zsh, you can add
    something like the following in your rc file to start and
    execute the chosen command.

      rash-isearch(){
        eval "$(rash isearch)"
      }

    To pass long and complex query, give them after "--",
    like this.::

      rash isearch -- \
        --cwd . \
        --exclude-pattern "*rash *" \
        --include-pattern "*test*" \
        --include-pattern "tox*" \
        --include-pattern "make *test*"

    """
    from .config import ConfigStore
    from .interactive_search import launch_isearch
    launch_isearch(ConfigStore(), **kwds)


def isearch_add_arguments(parser):
    parser.add_argument(
        '--query', '-q', default=None,
        help='default query')
    parser.add_argument(
        '--query-template', default=None,
        help='Transform default query using Python string format.')
    parser.add_argument(
        'base_query', nargs='*', default=None,
        help="""
        The part of query that is not shown in UI and is impossible
        to rewrite in this session.  Useful for putting long and
        complex query.
        """)
    parser.add_argument(
        '--caret', default=None, type=int,
        help='caret position')


commands = [
    ('isearch', isearch_add_arguments, isearch_run),
]
