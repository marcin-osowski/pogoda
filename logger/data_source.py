import collections
import datetime
import io
import re
import threading
import time
import traceback

import config


class LastValueRead(object):
    """Thread safe. Returns the last value read."""

    def __init__(self):
        self._lock = threading.Lock()
        self._value = None
        self._timestamp = None

    def set(self, value):
        """Sets the currently held value."""
        with self._lock:
            self._value = value
            self._timestamp = datetime.datetime.utcnow()

    def get(self):
        """Returns the currently held value, or None."""
        value, _ = self.get_with_timestamp()
        return value

    def get_with_timestamp(self):
        """Returns the currently held value with timestamp, or None."""
        with self._lock:
            if self._value is None:
                # No data available.
                return None, None
            return self._value, self._timestamp


class WeatherDataSource(object):
    """Retrieves from device and stores all recent weather data. Singleton."""

    # The available readings.
    readings = collections.defaultdict(lambda: LastValueRead())

    # Reader thread spawn lock
    _lock = threading.Lock()

    @staticmethod
    def Start():
        """Starts the underlying reader thread (never terminates)."""
        with WeatherDataSource._lock:
            if hasattr(WeatherDataSource, "_reader_thread"):
                # Already initialized.
                return
            WeatherDataSource._reader_thread = threading.Thread(
                    target=WeatherDataSource._reader_loop)
            WeatherDataSource._reader_thread.setDaemon(True)
            WeatherDataSource._reader_thread.start()

    @staticmethod
    def _reader_loop():
        while True:
            try:
                WeatherDataSource._stream_reader()
            except:
                print("Problem while reading %s" % config.COMM_PORT)
                traceback.print_exc()
                time.sleep(30.0)
            print("Re-starting data source stream reader.")

    @staticmethod
    def _stream_reader():
        print("Opening %s" % config.COMM_PORT)
        with io.open(config.COMM_PORT, mode='rt', buffering=1, errors='replace') as stream:
            print("Opened %s" % config.COMM_PORT)
            while True:
                line = stream.readline()
                if not line:
                    raise RuntimeError("Input stream %s was terminated")
                line = line.strip()
                if not line:
                    # Empty line (except for newline character).
                    continue

                match = re.match("^([^:]+): ([0-9.]+)$", line)
                if not match:
                    # Damaged line.
                    continue
                kind = match.group(1)
                value = match.group(2)

                try:
                    value = float(value)
                except:
                    # Not a valid float value
                    continue

                # Store the value.
                WeatherDataSource.readings[kind].set(value)

# Start the thread
WeatherDataSource.Start()
