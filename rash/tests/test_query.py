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

from ..config import Configuration
from ..query import expand_query
from .utils import BaseTestCase


class TestExpandQuery(BaseTestCase):

    def setUp(self):
        self.config = Configuration()
        self.config.search.alias['test'] = ["--include-pattern", "*test*"]
        self.config.search.alias['build'] = ["--include-pattern", "*build*"]

    def test_alias_no_query_no_expansion(self):
        kwds = expand_query(self.config, {})
        self.assertEqual(kwds.get('include_pattern', []), [])
        self.assertEqual(kwds['pattern'], [])

    def test_alias_expansion(self):
        kwds = expand_query(self.config, {'pattern': ['test']})
        self.assertEqual(kwds['include_pattern'], ['*test*'])
        self.assertEqual(kwds['pattern'], [])

    def test_alias_should_add_option(self):
        kwds = expand_query(self.config, {'include_pattern': ['*make*'],
                                          'pattern': ['test']})
        self.assertEqual(kwds['include_pattern'], ['*make*', '*test*'])
        self.assertEqual(kwds['pattern'], [])

    def test_alias_two_expansions(self):
        kwds = expand_query(self.config, {'pattern': ['test', 'build']})
        self.assertEqual(kwds['include_pattern'], ['*test*', '*build*'])
        self.assertEqual(kwds['pattern'], [])
