# Logger settings.
COMM_PORT="/dev/ttyUSB0"
LOGGER_INTERVAL_SEC=120
NAME_TRANSLATION={
    "Humidity": "humidity",
    "Temperature": "temperature",
    "Water level": "water_level",
    "Pressure": "pressure",
}
# Limits RAM usage in case of DB unreachability.
MAX_QUEUE_SIZE=1024*1024

# Common settings.
GCP_CREDENTIALS="./gcp-credentials.json"
GCP_PROJECT="pogoda-240600"
GCP_KIND_PREFIX="reading:"

# Web server settings.
PROD_HTTP_HOST='127.0.0.1'
PROD_HTTP_PORT=8092

DEV_HTTP_HOST='127.0.0.1'
DEV_HTTP_PORT=8080
