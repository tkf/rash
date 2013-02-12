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

from .iterutils import repeat


def concat_expr(operator, conditions):
    """
    Concatenate `conditions` with `operator` and wrap it by ().

    It returns a string in a list or empty list, if `conditions` is empty.

    """
    expr = " {0} ".format(operator).join(conditions)
    return ["({0})".format(expr)] if expr else []


class SQLConstructor(object):

    """
    SQL constructor.

    >>> sc = SQLConstructor('table', ['c1', 'c2'])
    >>> (sql, params, keys) = sc.compile()
    >>> sql
    'SELECT c1, c2 FROM table'

    >>> sc.add_or_matches('{0} = {1}', 'c1', [111, 222])
    >>> (sql, params, keys) = sc.compile()
    >>> sql
    'SELECT c1, c2 FROM table WHERE (c1 = ? OR c1 = ?)'
    >>> params
    [111, 222]

    """

    def __init__(self, join_source, columns, keys=None,
                group_by=None, order_by=None, reverse=False, limit=None):
        self.join_source = join_source
        self.columns = columns[:]
        self.keys = columns[:] if keys is None else keys[:]
        self.group_by = group_by or []
        self.order_by = order_by
        self.reverse = reverse
        self.limit = limit

        self.params = []
        self.conditions = []

    @property
    def sql_where(self):
        if self.conditions:
            return 'WHERE {0}'.format(" AND ".join(self.conditions))

    @property
    def sql_group_by(self):
        if self.group_by:
            return 'GROUP BY {0}'.format(', '.join(self.group_by))

    @property
    def sql_order_by(self):
        if self.order_by:
            direction = 'ASC' if self.reverse else 'DESC'
            return 'ORDER BY {0} {1}'.format(self.order_by, direction)

    sql_limit = ''

    @property
    def sql(self):
        return ' '.join(filter(None, [
            'SELECT', ', '.join(self.columns), 'FROM', self.join_source,
            self.sql_where,
            self.sql_group_by,
            self.sql_order_by,
            self.sql_limit,
        ]))

    def compile(self):
        if self.limit and self.limit >= 0:
            self.sql_limit = 'LIMIT ?'
            self.params.append(self.limit)
        return (self.sql, self.params, self.keys)

    @staticmethod
    def _adapt_params(params):
        if isinstance(params, (tuple, list)):
            return params
        elif params is None:
            return []
        else:
            return [params]

    @staticmethod
    def _adapt_matcher(matcher):
        if isinstance(matcher, str):
            return matcher.format
        else:
            return matcher

    def add_and_matches(self, matcher, lhs, params):
        params = self._adapt_params(params)
        expr = repeat(self._adapt_matcher(matcher)(lhs, '?'), len(params))
        self.conditions.extend(expr)
        self.params.extend(params)

    def add_or_matches(self, matcher, lhs, params):
        params = self._adapt_params(params)
        expr = repeat(self._adapt_matcher(matcher)(lhs, '?'), len(params))
        self.conditions.extend(concat_expr('OR', expr))
        self.params.extend(params)

    def add_matches(self, matcher, lhs,
                    match_params=[], include_params=[], exclude_params=[]):
        matcher = self._adapt_matcher(matcher)
        notmatcher = lambda x, y: 'NOT ' + matcher(x, y)
        self.add_and_matches(matcher, lhs, match_params)
        self.add_or_matches(matcher, lhs, include_params)
        self.add_and_matches(notmatcher, lhs, exclude_params)

    def uniquify_by(self, column, chooser=None, aggregate='MAX'):
        self.group_by.append(column)
        if chooser:
            i = self.columns.index(chooser)
            self.columns[i] = '{0}({1})'.format(aggregate, self.columns[i])

    def add_column(self, column, key=None):
        self.columns.append(column)
        self.keys.append(key or column)
