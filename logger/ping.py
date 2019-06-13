from datetime import datetime, timezone
import re
import sh
import time

import config
import instance_config


def get_host_latency(target, timeout_sec):
    """Pings the target server and returns the response time, in seconds.

    Returns None if there's no response within the timeout."""
    try:
        ping_result = sh.ping(target, c=1, W=timeout_sec)
    except:
        # Ignore exceptions.
        ping_result = ""

    parse_regex = r"^[0-9]+ bytes from .*: icmp_seq=[0-9]+ ttl=[0-9]+ time=([0-9.]+) ms$"
    for line in ping_result.split("\n"):
        match = re.match(parse_regex, line)
        if match:
            latency_msec = float(match.group(1))
            latency_sec = latency_msec / 1000.0
            return latency_sec

    return None


def get_internet_latency():
    """Tests latency versus several targets, returns min response time.

    Tests several targets to remove uncertaintity around target host
    being temporarily down.

    Returns None if none of the servers were reachable.
    """
    hosts = [
        "8.8.8.8",
        "8.8.4.4",
        "1.1.1.1",
        "1.0.0.1",
    ]
    latency = None
    for host in hosts:
        host_latency = get_host_latency(target=host, timeout_sec=1)
        if host_latency is None:
            # Target unreachable.
            continue
        if latency is None:
            # First successful reading.
            latency = host_latency
            continue
        latency = min(latency, host_latency)

    return latency


def scrape_conn_quality_once(data_queue, logger_statistics):
    internet_latency = get_internet_latency()
    if internet_latency is not None:
        timestamp = datetime.now(timezone.utc)
        kind = (instance_config.GCP_INSTANCE_NAME_PREFIX +
                config.GCP_CONN_QUALITY_PREFIX +
                "internet_latency")
        data_queue.put(
            timestamp=timestamp,
            kind=kind,
            value=internet_latency,
        )


def conn_quality_scraper_loop(data_queue, logger_statistics):
    """A continuous scraper of connection quality data.

    Should be running in a separate daemon thread."""

    while True:
        try:
            time.sleep(config.LOGGER_INTERVAL_SEC)
            if data_queue.qsize() >= config.MAX_QUEUE_SIZE:
                # Dropping data, queue too long
                pass
            else:
                scrape_conn_quality_once(data_queue, logger_statistics)
        except Exception as e:
            print("Problem while getting connection quality data.")
            print(e)
            time.sleep(60.0)
