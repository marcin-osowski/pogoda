#!/usr/bin/env python3

import datetime
from google.cloud import datastore
import os
import queue
import threading
import time
import traceback

import config
import instance_config
import data_source


# Readings queue - will be filled with data
# read from the sensors, to be written to the DB.
readings_queue = queue.Queue()


def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def get_and_push_readings_queue(weather_data):
    """Retrieves data and inserts it into the readings queue, once."""
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
        readings_queue.put((name, value, timestamp))


def readings_queue_producer_loop():
    # Uses a backgroud thread to read values from the serial port.
    weather_data = data_source.WeatherDataSource

    while True:
        try:
            time.sleep(config.LOGGER_INTERVAL_SEC)
            if readings_queue.qsize() >= config.MAX_QUEUE_SIZE:
                # Dropping data, queue too long.
                pass
            else:
                get_and_push_readings_queue(weather_data, readings_queue)
        except Exception as e:
            print("Problem while inserting data to the readings queue.")
            print(e)
            time.sleep(60.0)


def insert_into_db(client, name, value, timestamp):
    """Inserts a single reading into the DB."""
    key = client.key(
        instance_config.GCP_INSTANCE_NAME_PREFIX +
        config.GCP_READING_PREFIX +
        name)
    reading_ent = datastore.Entity(key)
    reading_ent.update(dict(
        timestamp=timestamp,
        value=value,
    ))
    client.put(reading_ent)


def readings_queue_consumer_loop():
    """A loop for popping items from the readings queue and inserting them into the DB."""
    while True:
        try:
            client = create_datastore_client()
            while True:
                name, value, timestamp = readings_queue.get()
                written = False
                try:
                    insert_into_db(client, name, value, timestamp)
                    written = True
                finally:
                    if not written:
                        # Put back in the readings queue
                        readings_queue.put((name, value, timestamp))
        except Exception as e:
            print("Problem while inserting data into the DB.")
            print(e)
            time.sleep(120.0)


if __name__ == "__main__":
    # Start a background thread to push values to the readings queue.
    producer_thread = threading.Thread(target=readings_queue_producer_loop)
    producer_thread.setDaemon(True)
    producer_thread.start()


    # Start popping items from the readings queue and inserting them into the DB.
    readings_queue_consumer_loop()

