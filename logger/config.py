import os.path

# Helper, since this is needed in a few places.
# The directory containing this config file.
this_directory=os.path.dirname(os.path.realpath(__file__))


#
# LOGGER
#

# Interval for scraping the Arduino readings data.
LOGGER_INTERVAL_SEC=120.0

# How often logger process stats (such as DB latency, success
# rate, internet latency) should be collected and put into the
# DB queue.
LOGGER_STATS_INTERVAL_SEC=10.0 * 60.0

# When in dry run logger will print data to stdout
# instead of pushing it to the cloud DB.
LOGGER_DRY_RUN=False

#
# ARDUINO
#

# The port with Arduino data stream.
COMM_PORT="/dev/ttyUSB0"


#
# IN-MEMORY QUEUE
#

# Limits RAM usage in case of DB unreachability.
# Approximate limit.
MAX_QUEUE_SIZE=256*1024


#
# LOCAL DISK DATABASE BUFFER
#

# Local SQLite database settings.
# Used to buffer data.
SQLITE_DB_FILENAME="db_buffer.sqlite3"

# Full file path for the SQLite DB.
SQLITE_DB_FILE=os.path.join(this_directory, SQLITE_DB_FILENAME)

# Start moving items from the queue to the sqlite DB
# when queue gets this long, or longer.
SQLITE_DUMP_QUEUE_LENGTH=150

# Dump this many items at once.
SQLITE_DUMP_AMOUNT=50

# Start fetching items from SQLite into the
# queue when it gets this short, or shorter.
SQLITE_FETCH_QUEUE_LENGTH=10

# Fetch this many items at once.
SQLITE_FETCH_AMOUNT=50


#
# CLOUD DATABASE
#

# Credentials to authenticate.
GCP_CREDENTIALS=os.path.join(this_directory, "gcp-credentials.json")

# GCP project.
GCP_PROJECT="pogoda-240600"

# Cloud database schema settings.

# The entity kind for a sensor reading is fully specified as:
#    instance_config.GCP_INSTANCE_NAME_PREFIX +
#    GCP_READING_PREFIX +
#    GCP_READING_NAME_TRANSLATION.value
GCP_READING_PREFIX="reading:"
GCP_READING_NAME_TRANSLATION={
    "Humidity": "humidity",
    "Temperature": "temperature",
    "Water level": "water_level",
    "Pressure": "pressure",

    "PM 1.0 standard": "pm_10_std",
    "PM 2.5 standard": "pm_25_std",
    "PM 10.0 standard": "pm_100_std",
    "PM 1.0 environmental": "pm_10_env",
    "PM 2.5 environmental": "pm_25_env",
    "PM 10.0 environmental": "pm_100_env",

    "Particles > 0.3um / 0.1L air": "particles_03",
    "Particles > 0.5um / 0.1L air": "particles_05",
    "Particles > 1.0um / 0.1L air": "particles_10",
    "Particles > 2.5um / 0.1L air": "particles_25",
    "Particles > 5.0um / 0.1L air": "particles_50",
    "Particles > 10.0 um / 0.1L air": "particles_100",

    "Wind speed": "wind_speed",
    "Wind direction": "wind_direction",
    # Rain mm is a cumulative output. Any time it gets
    # lower than a previous output it implies a device
    # reset, and the value by which it dropped down needs
    # to be added.
    "Total rain": "total_rain_mm",
}

# The entity kind for connection quality data is fully specified as:
#    instance_config.GCP_INSTANCE_NAME_PREFIX +
#    GCP_CONN_QUALITY_PREFIX +
#    "internet_latency"
GCP_CONN_QUALITY_PREFIX="connection:"
