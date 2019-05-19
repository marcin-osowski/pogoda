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
            # Value is missing, ignore.
            continue
        if timestamp is None:
            # Timestamp is missing, ignore.
            continue
        latency = datetime.datetime.utcnow() - timestamp
        if latency >= datetime.timedelta(seconds=config.LOGGER_INTERVAL_SEC):
            # Data too old
            continue
        data_queue.put((name, value, timestamp))


def queue_producer_loop(data_queue):
    # Uses a backgroud thread to read values from the serial port.
    weather_data = data_source.WeatherDataSource

    while True:
        try:
            time.sleep(config.LOGGER_INTERVAL_SEC)
            if data_queue.qsize() >= config.MAX_QUEUE_SIZE:
                # Dropping data, queue too long.
                pass
            else:
                get_and_push_queue(weather_data, data_queue)
        except:
            print("Problem while inserting data to the queue.")
            traceback.print_exc()
            time.sleep(60.0)


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
    """A loop for popping items from the queue and inserting them into the DB."""
    while True:
        try:
            client = create_datastore_client()
            while True:
                name, value, timestamp = data_queue.get()
                written = False
                try:
                    insert_into_db(client, name, value, timestamp)
                    written = True
                finally:
                    if not written:
                        # Put back in the queue
                        data_queue.put((name, value, timestamp))
        except:
            print("Problem while inserting data into the DB.")
            traceback.print_exc()
            time.sleep(120.0)


def queue_monitor_loop(data_queue):
    """A thread to monitor the state of the queue

    Checks every 45 minutes how many elements are pending.
    If there's more than 25 elements pending then prints
    a warning message.
    """
    while True:
        time.sleep(45.0 * 60.0)
        size = data_queue.qsize()
        if size > 25:
            print("%s: Warning: %d elements pending in the DB queue" % (
                    datetime.datetime.now().isoformat(" "),
                    size))


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

    # Start a background thread to monitor the queue.
    monitor_thread = threading.Thread(
            target=queue_monitor_loop,
            kwargs=dict(data_queue=data_queue),
    )
    monitor_thread.setDaemon(True)
    monitor_thread.start()


    # Start popping items from the queue and inserting them into the DB.
    queue_consumer_loop(data_queue)

