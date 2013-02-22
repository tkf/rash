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
import sys
PY3 = (sys.version_info[0] >= 3)

try:
    getcwd = os.getcwdu
except AttributeError:
    getcwd = os.getcwd


try:
    from contextlib import nested
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def nested(*managers):
        if managers:
            with managers[0] as ctx:
                with nested(*managers[1:]) as rest:
                    yield (ctx,) + rest
        else:
            yield ()

try:
    from itertools import izip_longest as zip_longest
except ImportError:
    from itertools import zip_longest

try:
    from itertools import izip as zip
except ImportError:
    zip = zip
