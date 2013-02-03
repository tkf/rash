import time
import signal

try:
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler, FileCreatedEvent)
except ImportError:
    FileSystemEventHandler = object


class RecordHandler(FileSystemEventHandler):

    def __init__(self, indexer, **kwds):
        self.__indexer = indexer
        super(RecordHandler, self).__init__(**kwds)

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            self.__indexer.index_record(event.src_path)


def watch_record(indexer):
    """
    Start watching `conf.record_path`.

    :type indexer: rash.indexer.Indexer

    """

    def handle_sigterm(_signum, _frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, handle_sigterm)

    event_handler = RecordHandler(indexer)
    observer = Observer()
    observer.schedule(event_handler, path=indexer.record_path, recursive=True)
    indexer.logging.debug('Start observer.')
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        indexer.logging.debug('Got KeyboardInterrupt. Stopping observer.')
        observer.stop()
    indexer.logging.debug('Joining observer.')
    observer.join()
    indexer.logging.debug('Finish watching record.')
