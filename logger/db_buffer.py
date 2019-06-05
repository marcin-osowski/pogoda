from datetime import datetime, timezone
import sqlite3
import threading
import time

import config


class SQLiteBuffer(object):
    """A helper class to spill over queue elements to the SQLite DB.

    This clas both spills over extra elements and returns them
    from the SQLite DB.

    Timestamps are written without timezone info (as UTC)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            config.SQLITE_DB_FILE,
            detect_types=sqlite3.PARSE_DECLTYPES)
        self._rebuild_schema()
        self._recount_elements()

    def rows_in_db(self):
        with self._lock:
            return self._rows_in_db

    def dump_to_sqlite(self, data_queue):
        """Writes excessive elements from the data queue to the SQLite DB."""
        elements = []
        try:
            # Get elements from the queue.
            for i in range(config.SQLITE_DUMP_AMOUNT):
                data = data_queue.get_oldest_nowait()
                if data is None:
                    # No more data in the queue.
                    break
                timestamp, kind, value = data
                elements.append((timestamp, kind, value))

            # Dump them to SQLite.
            with self._lock:
                with self._conn:
                    elements_no_timezone = []
                    for timestamp, kind, value in elements:
                        # Strip the timezone data from the timestamp
                        assert timestamp.tzinfo == timezone.utc, "Non-UTC timestamp."
                        timestamp = timestamp.replace(tzinfo=None)
                        elements_no_timezone.append((timestamp, kind, value))

                    # Write to the DB.
                    self._conn.executemany("""
                        INSERT INTO data_buffer (timestamp, kind, value)
                        VALUES ((?), (?), (?))
                    """, elements_no_timezone)

                # All good (transaction committed), update variables.
                self._rows_in_db += len(elements)
                elements = []

        finally:
            for timestamp, kind, value in elements:
                # Return unused elements.
                data_queue.put_return(timestamp, kind, value)

    def fetch_from_sqlite(self, data_queue):
        with self._lock:
            elements = []
            with self._conn:
                # Get elements from the DB.
                cur = self._conn.cursor()
                cur.execute("""
                    SELECT id, timestamp, kind, value
                    FROM data_buffer
                    LIMIT (?)
                """, (config.SQLITE_FETCH_AMOUNT,))

                # Massage data, extract IDs
                ids_to_remove = []
                for db_id, timestamp, kind, value in cur:
                    ids_to_remove.append((db_id,))
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                    elements.append((timestamp, kind, value))

                # Drop IDs
                cur.executemany("""
                    DELETE FROM data_buffer
                    WHERE id = (?)
                """, ids_to_remove)

            # All good (transaction committed), update variables.
            self._rows_in_db -= len(elements)

            # Push elements to the queue
            for timestamp, kind, value in elements:
                data_queue.put_return(timestamp, kind, value)

    # Private functions.

    def _recount_elements(self):
        """Re-counts elements in the DB.

        Needs to be called only once, at startup."""
        with self._lock:
            with self._conn:
                cur = self._conn.cursor()
                cur.execute("""
                    SELECT count(*)
                    FROM data_buffer
                """)
                (self._rows_in_db,) = cur.fetchone()

    def _rebuild_schema(self):
        """Re-build schema in the DB.

        Does nothing if the table is already there.

        Needs to be called only once, at startup."""
        with self._lock:
            with self._conn:
                self._conn.execute("""
CREATE TABLE IF NOT EXISTS data_buffer (
    id        INTEGER   PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    kind      TEXT      NOT NULL,
    value     REAL      NOT NULL
)""")


def sqlite_buffer_loop(data_queue):
    while True:
        sqlite_buffer = SQLiteBuffer()
        try:
            while True:
                qsize = data_queue.qsize()
                if qsize >= config.SQLITE_DUMP_QUEUE_LENGTH:
                    sqlite_buffer.dump_to_sqlite(data_queue)
                if qsize <= config.SQLITE_FETCH_QUEUE_LENGTH:
                    if sqlite_buffer.rows_in_db() > 0:
                        sqlite_buffer.fetch_from_sqlite(data_queue)

                # Wait a little before the next iteration.
                # This should ideally block on qsize() changing value.
                time.sleep(5.0)
        except Exception as e:
            print("Problem with the SQLite buffer.")
            print(e)
            time.sleep(120.0)


def count_sqlite_elements():
    """A utility function that counts the number of DB elements."""
    conn = sqlite3.connect(config.SQLITE_DB_FILE)
    with conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT count(*)
            FROM data_buffer
        """)
        (rows,) = cur.fetchone()
        return rows
