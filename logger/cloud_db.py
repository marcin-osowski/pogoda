from google.cloud import datastore
import os
import time

import config


def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def insert_into_cloud_db(client, timestamp, kind, value):
    """Inserts a single entry into the cloud DB."""
    key = client.key(kind)
    reading_ent = datastore.Entity(key)
    reading_ent.update(dict(timestamp=timestamp))
    if value is not None:
        reading_ent.update(dict(value=value))
    client.put(reading_ent)


def cloud_uploader_loop(data_queue):
    """A loop: popping items from queue, inserting them into the cloud DB."""
    while True:
        try:
            client = create_datastore_client()
            while True:
                timestamp, kind, value = data_queue.get_youngest()
                written = False
                try:
                    insert_into_cloud_db(client, timestamp, kind, value)
                    written = True
                finally:
                    if not written:
                        # Put back in the readings queue
                        data_queue.put_return(timestamp, kind, value)
        except Exception as e:
            print("Problem while inserting data into the cloud DB.")
            print(e)
            time.sleep(120.0)

