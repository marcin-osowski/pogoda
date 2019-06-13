from datetime import datetime,timezone
from google.cloud import datastore
import os
import time

import config


def create_datastore_client():
    """Creates a Client, to connect to the Datastore DB."""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.GCP_CREDENTIALS
    return datastore.Client(project=config.GCP_PROJECT)


def insert_into_cloud_db(client, elements):
    """Inserts entries into the cloud DB."""
    ents = []
    for timestamp, kind, value in elements:
        key = client.key(kind)
        ent = datastore.Entity(key)
        ent.update(dict(timestamp=timestamp))
        if value is not None:
            ent.update(dict(value=value))
        ents.append(ent)
    if ents:
        client.put_multi(ents)


def cloud_uploader_loop(data_queue, logger_statistics):
    """A loop: popping items from queue, inserting them into the cloud DB.

    If there's multiple items pending in the queue it will attempt to move
    to the cloud DB a few items at a time.
    """
    while True:
        try:
            client = create_datastore_client()
            while True:
                # Get one element from the queue.
                elements = []
                timestamp, kind, value = data_queue.get_youngest()
                elements.append((timestamp, kind, value))

                # Try to get extra 9 elements for a total of max 10
                # if there's anything else in the queue. This speeds
                # up bulk upload of data.
                for i in range(9):
                    data = data_queue.get_youngest_nowait()
                    if data is None:
                        break
                    timestamp, kind, value = data
                    elements.append((timestamp, kind, value))

                # Try to write.
                written = False
                time_start = datetime.now(timezone.utc)
                try:
                    insert_into_cloud_db(client, elements)
                    written = True
                finally:
                    if written:
                        # Record the success.
                        db_latency = datetime.now(timezone.utc) - time_start
                        logger_statistics.cloud_db_write_result(
                            success=True,
                            latency=db_latency.total_seconds(),
                            elements=len(elements),
                        )
                    else:
                        # Put back elements in the readings queue
                        for timestamp, kind, value in elements:
                            data_queue.put_return(timestamp, kind, value)
                        # Record the failure.
                        logger_statistics.cloud_db_write_result(success=False)

        except Exception as e:
            print("Problem while inserting data into the cloud DB.")
            print(e)
            time.sleep(120.0)

