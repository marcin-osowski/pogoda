#!/usr/bin/env python3

import datetime
from google.cloud import datastore
import os
import queue
import threading
import time
import traceback

import config
import data_source

def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)

def get_and_push_queue(weather_data, data_queue):
    """Retrieves data and inserts it into a queue, once."""
    for comm_name, name in config.NAME_TRANSLATION.items():
        value, timestamp = weather_data.readings[comm_name].get_with_timestamp()
        if value is None:
            return
        if timestamp is None:
            return
        latency = datetime.datetime.utcnow() - timestamp
        if latency >= datetime.timedelta(seconds=config.LOGGER_INTERVAL_SEC):
            # Data too old
            return
        data_queue.put((name, value, timestamp))

def queue_producer_loop(data_queue):
    # Uses a backgroud thread to read values from the serial port.
    weather_data = data_source.WeatherDataSource

    # Sleep at start, so that the serial port values settle
    time.sleep(5.0)

    while True:
        try:
            get_and_push_queue(weather_data, data_queue)
        except:
            print("Problem while inserting data to the queue.")
            traceback.print_exc()
        time.sleep(config.LOGGER_INTERVAL_SEC)

def insert_into_db(client, name, value, timestamp):
    """Inserts a single reading into the DB."""
    key = client.key(config.GCP_KIND_PREFIX + name)
    reading_ent = datastore.Entity(key)
    reading_ent.update(dict(
        timestamp=timestamp,
        value=value,
    ))
    client.put(reading_ent)

def queue_consumer_loop(data_queue):
    """A loop for popping items from the queue and inserting them into the DB.

    Note: this will drop a single item on each DB error."""
    while True:
        try:
            client = create_datastore_client()
            while True:
                name, value, timestamp = data_queue.get()
                insert_into_db(client, name, value, timestamp)
        except:
            print("Problem while inserting data into the DB.")
            traceback.print_exc()
        time.sleep(config.LOGGER_INTERVAL_SEC + 60)

if __name__ == "__main__":
    # Queue - will be filled with data to be written to the DB.
    data_queue = queue.Queue()

    # Start a background thread to push values to the queue.
    producer_thread = threading.Thread(
            target=queue_producer_loop,
            kwargs=dict(data_queue=data_queue),
    )
    producer_thread.setDaemon(True)
    producer_thread.start()

    # Start popping items from the queue and inserting them into the DB.
    queue_consumer_loop(data_queue)

