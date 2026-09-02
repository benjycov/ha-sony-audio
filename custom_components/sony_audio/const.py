"""Constants for Sony Audio."""

from datetime import timedelta

DOMAIN = "sony_audio"
CONF_ENDPOINT = "endpoint"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=15)
DEFAULT_API_PORT = 10000
DEFAULT_API_PATH = "/sony"
ERROR_REQUEST_RETRY = 40000

MAIN_ZONE_TITLES = frozenset({"main", "main zone", "zone 1"})
