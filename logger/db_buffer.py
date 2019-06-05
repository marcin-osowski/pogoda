import sqlite3

import config

class SQLiteBuffer(object):

    def __init__(self):
        self._conn = sqlite3.connect(config.SQLITE_DB_FILE)
        self.count_elements()

    def count_elements(self):
        print("count_elements")

    def dump_to_sqlite(self, data_queue):
        print("dump_to_sqlite")

    def fetch_from_sqlite(self, data_queue):
        print("fetch_from_sqlite")


def sqlite_buffer_loop(data_queue):
    while True:
        try:
            sqlite_buffer = SQLiteBuffer()
            while True:
                qsize = data_queue.qsize()
                if qsize >= config.SQLITE_DUMP_QUEUE_LENGTH:
                    sqlite_buffer.dump_to_sqlite(data_queue)
                if qsize <= config.SQLITE_FETCH_QUEUE_LENGTH:
                    sqlite_buffer.fetch_from_sqlite(data_queue)
                time.sleep(10.0)
        except Exception as e:
            print("Problem with the SQLite buffer.")
            print(e)
            time.sleep(120.0)

