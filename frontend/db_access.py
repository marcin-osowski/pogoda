from google.cloud import datastore
import os

import config


def create_datastore_client():
    """Creates a Datastore Client object."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def get_latest_reading(client, name):
    """Returns the value and timestamp of the latest reading."""
    query = client.query(kind=name)
    query.order = ["-timestamp"]
    results = list(query.fetch(limit=1))

    if not results:
        return None, None
    result = results[0]
    if "value" not in result:
        return None, None
    value = result["value"]
    if "timestamp" not in result:
        return None, None
    timestamp = result["timestamp"]

    return value, timestamp


def get_last_readings(client, name, time_from, time_to):
    """Returns values and timestamps of recent readings."""
    query = client.query(kind=name)
    query.add_filter("timestamp", ">=", time_from)
    query.add_filter("timestamp", "<=", time_to)
    query.order = ["timestamp"]

    parsed_results = []
    for entity in query.fetch():
        if "value" not in entity:
            continue
        if "timestamp" not in entity:
            continue
        parsed_results.append((entity["value"], entity["timestamp"]))
    return parsed_results


