#!/usr/bin/env python3

import datetime
from google.cloud import datastore
import os


# Copies all values from SOURCE_SERIES
# into TARGET_SERIES.
SOURCE_SERIES=""
TARGET_SERIES=""


def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./gcp-credentials.json"
    return datastore.Client(project="pogoda-240600")


def get_series(client, name):
    query = client.query(kind=name)
    parsed_results = []
    for entity in query.fetch():
        if "value" not in entity:
            continue
        if "timestamp" not in entity:
            continue
        parsed_results.append((entity["value"], entity["timestamp"]))
    return parsed_results


def upload_series(client, name, series):
    entities = []
    for i, (value, timestamp) in enumerate(series):
        key = client.key(name)
        entity = datastore.Entity(key)
        entity.update(dict(
            timestamp=timestamp,
            value=value,
        ))
        entities.append(entity)
        # Flush every 500 entities
        if (i + 1) % 500 == 0:
            print("Uploading %d entries" % len(entities))
            client.put_multi(entities)
            entities = []
    if entities:
        print("Uploading %d entries" % len(entities))
        client.put_multi(entities)
        entities = []


def copy_series():
    client = create_datastore_client()

    print("Getting entries for %s" % SOURCE_SERIES)
    series = get_series(client, SOURCE_SERIES)
    print("Got %d entries" % len(series))

    print("Uploading into %s" % TARGET_SERIES)
    upload_series(client, TARGET_SERIES, series)
    print("Done")


if __name__ == "__main__":
    assert SOURCE_SERIES
    assert TARGET_SERIES

    print("Attempting to copy all values from \"%s\" into \"%s\"." %
        (SOURCE_SERIES, TARGET_SERIES))
    if input("Are you sure (y/n) ") == "y":
        copy_series()
