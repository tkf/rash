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


import os
import tempfile
import shutil
import json

from ..config import ConfigStore
from ..indexer import Indexer
from ..utils.pathutils import mkdirp
from .utils import BaseTestCase


class TestIndexer(BaseTestCase):

    def setUp(self):
        self.base_path = tempfile.mkdtemp(prefix='rash-test-')
        self.cfstore = ConfigStore(self.base_path)

    def tearDown(self):
        shutil.rmtree(self.base_path)

    def get_indexer(self, keep_json=True, check_duplicate=True):
        return Indexer(self.cfstore, check_duplicate, keep_json)

    def prepare_records(self, **records):
        if set(records) > set(['command', 'init', 'exit']):
            raise ValueError(
                'Unknown record type in {0}'.format(list(records)))
        paths = []
        for (rectype, data_list) in records.items():
            for (i, data) in enumerate(data_list):
                json_path = os.path.join(self.cfstore.record_path,
                                         rectype,
                                         '{0:05d}.json'.format(i))
                mkdirp(os.path.dirname(json_path))
                with open(json_path, 'w') as f:
                    json.dump(data, f)
                paths.append(json_path)
        return paths

    def get_dummy_records(self, num_command=1, num_init=1, num_exit=1):
        gen = lambda i, **kwds: dict(session_id='SID-{0}'.format(i), **kwds)
        return dict(
            command=[gen(i, start=i, stop=i + 1) for i in range(num_command)],
            init=[gen(i, start=i) for i in range(num_init)],
            exit=[gen(i, stop=i) for i in range(num_exit)],
        )

    def test_find_record_files(self):
        indexer = self.get_indexer()
        self.assertEqual(list(indexer.find_record_files()), [])
        desired_paths = self.prepare_records(**self.get_dummy_records())
        actual_paths = list(indexer.find_record_files())
        self.assertSetEqual(set(actual_paths), set(desired_paths))

    def test_index_all_and_keep_json(self):
        desired_paths = self.prepare_records(**self.get_dummy_records())
        indexer = self.get_indexer()
        indexer.index_all()
        actual_paths = list(indexer.find_record_files())
        self.assertSetEqual(set(actual_paths), set(desired_paths))

    def test_index_all_and_discard_json(self):
        self.prepare_records(**self.get_dummy_records())
        indexer = self.get_indexer(keep_json=False)
        indexer.index_all()
        actual_paths = list(indexer.find_record_files())
        self.assertEqual(actual_paths, [])
