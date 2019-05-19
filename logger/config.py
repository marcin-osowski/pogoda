COMM_PORT="/dev/ttyUSB0"
LOGGER_INTERVAL_SEC=120
NAME_TRANSLATION={
    "Humidity": "humidity",
    "Temperature": "temperature",
    "Water level": "water_level",
    "Pressure": "pressure",
}

# Limits RAM usage in case of DB unreachability.
# Approximate limit.
MAX_QUEUE_SIZE=1024*1024

# Database settings.
GCP_CREDENTIALS="./gcp-credentials.json"
GCP_PROJECT="pogoda-240600"
GCP_KIND_PREFIX="reading:"
