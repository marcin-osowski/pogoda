#!/usr/bin/env python3

from datetime import datetime, timezone
import threading
import time

import arduino_interface
import cloud_db
import config
import custom_queue
import db_buffer
import logger_stats
import ping


if __name__ == "__main__":
    if config.LOGGER_DRY_RUN:
        print()
        print("Warning")
        print("Running in dry run mode. No data will be written to the cloud DB.")
        print()

    # A queue with data to be written to the DB.
    data_queue = custom_queue.CustomQueue()

    # Logger statistics.
    logger_statistics = logger_stats.LoggerStatistics()

    def thread_kickoff(target, **kwargs):
        kwargs["data_queue"] = data_queue
        kwargs["logger_statistics"] = logger_statistics
        thread = threading.Thread(
            target=target,
            kwargs=kwargs,
        )
        thread.setDaemon(True)
        thread.start()

    # Start a thread to scrape Arduino data.
    arduino_scraper_thread = thread_kickoff(
        target=arduino_interface.arduino_scraper_loop,
    )

    # Start a thread to scrape connection quality data.
    conn_quality_scraper_thread = thread_kickoff(
        target=ping.conn_quality_scraper_loop,
    )

    # Start popping items from the readings queue
    # and inserting them into the DB.
    cloud_uploader_thread = thread_kickoff(
        target=cloud_db.cloud_uploader_loop,
    )

    # Start the SQLite DB buffer thread.
    sqlite_buffer_thread = thread_kickoff(
        target=db_buffer.sqlite_buffer_loop,
    )

    # Start the statistics writer thread.
    logger_statistics_thread = thread_kickoff(
        target=logger_statistics.statistics_writer_thread,
    )

    # Show the "user menu".
    time.sleep(10.0)
    while True:
        try:
            input("Press enter to show stats ")
            print()

            # Gather data.
            elements_in_queue = data_queue.qsize()
            number_of_new_readings = logger_statistics.number_of_new_readings()
            cloud_db_elements_written = logger_statistics.cloud_db_elements_written()
            sqlite_elements = db_buffer.count_sqlite_elements()
            time_since_cloud_success = logger_statistics.cloud_db_time_since_success()
            time_since_cloud_failure = logger_statistics.cloud_db_time_since_failure()
            time_running = logger_statistics.time_running()

            # Show it
            print("Total number of elements written to cloud DB:",
                  cloud_db_elements_written)
            print("Total number of new readings:", number_of_new_readings)
            print("Elements currently in the queue:", elements_in_queue)
            print("Elements currently in the SQLite DB:", sqlite_elements)
            print("Time since last cloud DB write success:",
                  time_since_cloud_success)
            print("Time since last cloud DB write failure:",
                  time_since_cloud_failure)
            print("Program running (time):", time_running)
            print()

        except Exception as e:
            print("Problem in the user menu")
            print(e)
