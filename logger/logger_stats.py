from datetime import datetime, timezone
import threading
import time

import config
import instance_config

class LoggerStatistics(object):
    """A class that collects various logger statistics.

    Thread safe.

    Periodically writes statistics to the DB queue."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cloud_db_successes = []
        self._cloud_db_latencies = []
        self._number_of_new_readings = 0
        self._timestamp_start = datetime.now(timezone.utc)

    def cloud_db_write_result(self, success, latency_ms=None):
        """Saves a single cloud DB write result.

        If success is true latency must be passed (in ms)."""
        with self._lock:
            if success:
                self._cloud_db_successes.append(True)
                self._cloud_db_latencies.append(float(latency_ms))
            else:
                self._cloud_db_successes.append(False)

    def register_new_reading(self):
        """Registers a new reading."""
        with self._lock:
            self._number_of_new_readings += 1

    def number_of_new_readings(self):
        with self._lock:
            return self._number_of_new_readings

    def time_running(self):
        """Returns the total time running."""
        return datetime.now(timezone.utc) - self._timestamp_start

    def _get_and_clear_db_success_rate(self):
        with self._lock:
            if len(self._cloud_db_successes) < 5:
                # Not enough data collected.
                return None
            success_rate = (
                float(self._cloud_db_successes.count(True)) /
                float(len(self._cloud_db_successes))
            )
            self._cloud_db_successes = []
            return success_rate

    def _get_and_clear_avg_db_latency(self):
        with self._lock:
            if len(self._cloud_db_latencies) < 5:
                # Not enough data collected.
                return None
            avg_latency = (
                float(sum(self._cloud_db_latencies)) /
                float(len(self._cloud_db_latencies))
            )
            self._cloud_db_latencies = []
            return avg_latency

    def _put_stat(self, data_queue, name, value):
        timestamp = datetime.now(timezone.utc)
        kind = (instance_config.GCP_INSTANCE_NAME_PREFIX +
                config.GCP_CONN_QUALITY_PREFIX +
                name)
        data_queue.put(
            timestamp=timestamp,
            kind=kind,
            value=value)

    def _put_stats_once(self, data_queue):
        success_rate = self._get_and_clear_db_success_rate()
        self._put_stat(data_queue, "cloud_db_write_success_rate", success_rate)
        avg_latency = self._get_and_clear_avg_db_latency()
        self._put_stat(data_queue, "cloud_db_write_latency", avg_latency)

    def statistics_writer_thread(self, data_queue, logger_statistics):
        while True:
            try:
                time.sleep(config.LOGGER_STATS_INTERVAL_SEC)
                self._put_stats_once(data_queue)
            except Exception as e:
                print("Problem in the statistics writer thread.")
                print(e)
                time.sleep(120.0)

