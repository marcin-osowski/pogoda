#!/usr/bin/env python3

import datetime
from google.cloud import datastore
import os
import queue
import threading
import time

import arduino_interface
import config
import instance_config
import ping


# A queue with data to be written to the DB.
# Triples: DB kind (name), timestamp, value
data_queue = queue.Queue()


def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def get_readings(weather_data):
    """Retrieves readings and inserts it into the queue, once."""
    for comm_name, name in config.GCP_READING_NAME_TRANSLATION.items():
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
        kind = (instance_config.GCP_INSTANCE_NAME_PREFIX +
                config.GCP_READING_PREFIX +
                name)
        data_queue.put((kind, timestamp, value))


def readings_producer_loop():
    # Uses a backgroud thread to read values from the serial port.
    weather_data = arduino_interface.WeatherDataSource

    while True:
        try:
            time.sleep(config.LOGGER_INTERVAL_SEC)
            if data_queue.qsize() >= config.MAX_QUEUE_SIZE:
                # Dropping data, queue too long.
                pass
            else:
                get_readings(weather_data)
        except Exception as e:
            print("Problem while getting readings data.")
            print(e)
            time.sleep(60.0)


def get_conn_quality():
    internet_latency = ping.get_internet_latency()
    if internet_latency is not None:
        timestamp = datetime.datetime.utcnow()
        kind = (instance_config.GCP_INSTANCE_NAME_PREFIX +
                config.GCP_CONN_QUALITY_PREFIX +
                "internet_latency")
        data_queue.put((kind, timestamp, internet_latency))


def conn_quality_producer_loop():
    while True:
        try:
            if data_queue.qsize() >= config.MAX_QUEUE_SIZE:
                # Dropping data, queue too long
                pass
            else:
                get_conn_quality()
            time.sleep(config.LOGGER_INTERVAL_SEC)
        except Exception as e:
            print("Problem while getting connection quality data.")
            print(e)
            time.sleep(60.0)


def insert_into_cloud_db(client, kind, timestamp, value):
    """Inserts a single entry into the cloud DB."""
    key = client.key(kind)
    reading_ent = datastore.Entity(key)
    reading_ent.update(dict(timestamp=timestamp))
    if value is not None:
        reading_ent.update(dict(value=value))
    client.put(reading_ent)


def queue_consumer_loop():
    """A loop: popping items from queue, inserting them into the cloud DB."""
    while True:
        try:
            client = create_datastore_client()
            while True:
                kind, value, timestamp = data_queue.get()
                written = False
                try:
                    insert_into_cloud_db(client, kind, timestamp, value)
                    written = True
                finally:
                    if not written:
                        # Put back in the readings queue
                        readings_queue.put((kind, timestamp, value))
        except Exception as e:
            print("Problem while inserting data into the cloud DB.")
            print(e)
            time.sleep(120.0)


if __name__ == "__main__":
    # Start a background thread to push values to the readings queue.
    readings_producer_thread = threading.Thread(target=readings_producer_loop)
    readings_producer_thread.setDaemon(True)
    readings_producer_thread.start()

    # Start a background thread to push values to the connection quality queue.
    conn_producer_thread = threading.Thread(target=conn_quality_producer_loop)
    conn_producer_thread.setDaemon(True)
    conn_producer_thread.start()

    # Start popping items from the readings queue and inserting them into the DB.
    queue_consumer_loop()

