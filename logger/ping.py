import re
import sh


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
        host_latency = get_host_latency(target=host, timeout_sec=2.5)
        if host_latency is None:
            # Target unreachable.
            continue
        if latency is None:
            # First successful reading.
            latency = host_latency
            continue
        latency = min(latency, host_latency)

    return latency
