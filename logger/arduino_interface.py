import collections
from datetime import datetime, timedelta, timezone
import io
import re
import threading
import time

import config
import instance_config


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
            self._timestamp = datetime.now(timezone.utc)

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
    """Retrieves from device and stores all recent weather data."""

    def __init__(self):
        self._lock = threading.Lock()
        self._readings = collections.defaultdict(lambda: LastValueRead())

    def reader_loop(self, data_queue, logger_statistics):
        while True:
            try:
                self._stream_reader(data_queue, logger_statistics)
            except Exception as e:
                print("Problem while reading %s" % config.COMM_PORT)
                print(e)
                time.sleep(60.0)
            print("Re-starting data source stream reader.")

    def get_reading(self, key):
        """Returns a LastValueRead object for the key.

        Will be empty if there's no data under that key.
        """
        with self._lock:
            return self._readings[key]

    def _stream_reader(self, data_queue, logger_statistics):
        print("Opening Arduino comm port at", config.COMM_PORT)
        with io.open(config.COMM_PORT, mode='rt', buffering=1, errors='replace') as stream:
            print("Opened", config.COMM_PORT)
            while True:
                line = stream.readline()
                if not line:
                    raise RuntimeError("Input stream %s was terminated" % config.COMM_PORT)

                line = line.strip()
                if not line:
                    # Empty line (except for newline character).
                    continue

                # Update stats.
                logger_statistics.add_comm_lines_read()
                logger_statistics.add_comm_bytes_read(len(line))

                # Decompose the line into kind and value
                match = re.match("^([^:]+): ([0-9.]+)$", line)
                if not match:
                    # Damaged line.
                    continue
                kind = match.group(1)
                value = match.group(2)

                # Try to parse the value as a float.
                try:
                    value = float(value)
                except:
                    # Not a valid float value
                    continue

                # This line is parsed, log that.
                logger_statistics.add_comm_parsed_lines_read()

                # Store the value.
                with self._lock:
                    self._readings[kind].set(value)


    def _scrape_readings_once(self, data_queue, logger_statistics, last_timestamp_read):
        """Retrieves readings and inserts it into the queue, once."""
        for comm_name, name in config.GCP_READING_NAME_TRANSLATION.items():
            value, timestamp = self.get_reading(comm_name).get_with_timestamp()
            if value is None:
                # Value is missing, ignore.
                continue
            if timestamp is None:
                # Timestamp is missing, ignore.
                continue

            if comm_name in last_timestamp_read:
                if timestamp <= last_timestamp_read[comm_name]:
                    # Data has not changed since last access.
                    continue


            # Compute the DB kind.
            kind = (instance_config.GCP_INSTANCE_NAME_PREFIX +
                    config.GCP_READING_PREFIX +
                    name)

            # Push it.
            data_queue.put(
                timestamp=timestamp,
                kind=kind,
                value=value,
            )
            logger_statistics.register_new_reading()

            # Store last access timestamp.
            last_timestamp_read[comm_name] = datetime.now(timezone.utc)


    def scraper_loop(self, data_queue, logger_statistics):
        """Scrapes Arduino data periodically, pushes it to the queue.

        This function should be running in a separate daemon thread."""

        # The timestamp of the last value read from Arduino
        # and pushed onto the queue.
        # Format: comm_name -> datetime
        last_timestamp_read = dict()

        while True:
            try:
                # Wait for the next reading.
                time.sleep(config.LOGGER_INTERVAL_SEC)

                if data_queue.qsize() >= config.MAX_QUEUE_SIZE:
                    # Dropping data, queue too long.
                    pass
                else:
                    self._scrape_readings_once(data_queue, logger_statistics,
                                               last_timestamp_read)
            except Exception as e:
                print("Problem while getting readings data.")
                print(e)
                time.sleep(60.0)
