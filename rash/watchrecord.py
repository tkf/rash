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
import signal

try:
    from watchdog.events import (
        FileSystemEventHandler, FileCreatedEvent)
    assert FileSystemEventHandler  # fool pyflakes
except ImportError:
    # Dummy class for making this module importable:
    FileSystemEventHandler = object


class RecordHandler(FileSystemEventHandler):

    def __init__(self, indexer, **kwds):
        self.__indexer = indexer
        super(RecordHandler, self).__init__(**kwds)

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            self.__indexer.index_record(event.src_path)


def raise_keyboardinterrupt(_signum, _frame):
    raise KeyboardInterrupt


def install_sigterm_handler():
    signal.signal(signal.SIGTERM, raise_keyboardinterrupt)


def watch_record(indexer, use_polling=False):
    """
    Start watching `cfstore.record_path`.

    :type indexer: rash.indexer.Indexer

    """
    if use_polling:
        from watchdog.observers.polling import PollingObserver as Observer
        Observer  # fool pyflakes
    else:
        from watchdog.observers import Observer

    event_handler = RecordHandler(indexer)
    observer = Observer()
    observer.schedule(event_handler, path=indexer.record_path, recursive=True)
    indexer.logger.debug('Start observer.')
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        indexer.logger.debug('Got KeyboardInterrupt. Stopping observer.')
        observer.stop()
    indexer.logger.debug('Joining observer.')
    observer.join()
    indexer.logger.debug('Finish watching record.')
