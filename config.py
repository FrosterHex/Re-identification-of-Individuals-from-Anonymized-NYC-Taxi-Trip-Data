"""
config.py — Shared constants for the NYC Taxi Re-identification Attack Simulation.

This module defines:
  - Known NYC landmark coordinates used as auxiliary knowledge in the attack.
  - Medallion number format patterns (real NYC TLC format).
  - Default search parameters for the linkage attack.

References:
  Tockar, A. (2014). Riding with the stars: Passenger privacy in the NYC taxicab dataset.
"""

# ──────────────────────────────────────────────────────────────────────────────
# NYC Landmark Coordinates (Auxiliary Knowledge)
# These represent publicly-known locations an attacker might use.
# ──────────────────────────────────────────────────────────────────────────────

KNOWN_LOCATIONS = {
    "The Standard Hotel (Meatpacking)": {
        "lat": 40.7408,
        "lon": -74.0080,
        "description": "Nightclub/hotel frequently visited by celebrities. "
                       "Used in original Tockar (2014) research."
    },
    "JFK Airport Terminal 4": {
        "lat": 40.6413,
        "lon": -73.7781,
        "description": "Major international terminal — high-profile arrivals."
    },
    "Madison Square Garden": {
        "lat": 40.7505,
        "lon": -73.9934,
        "description": "Major event venue — attendees are often photographed entering/exiting."
    },
    "Trump Tower (5th Ave)": {
        "lat": 40.7624,
        "lon": -73.9738,
        "description": "High-profile residence with extensive paparazzi coverage."
    },
    "The Plaza Hotel": {
        "lat": 40.7645,
        "lon": -73.9744,
        "description": "Iconic luxury hotel — celebrity sightings are common."
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# NYC Taxi Medallion Format
# Real NYC medallions follow the pattern: <digit><letter><digit><digit>
# e.g., "1A01", "5Z99", "9B42"
# The TLC hashed these with unsalted MD5, making rainbow tables trivial.
# ──────────────────────────────────────────────────────────────────────────────

MEDALLION_DIGITS = "123456789"
MEDALLION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MEDALLION_PATTERN_DESC = "<digit><letter><digit><digit>  (e.g., '5Z42')"

# Hack license numbers in the real dataset were 6-digit numeric strings.
HACK_LICENSE_MIN = 100000
HACK_LICENSE_MAX = 999999

# ──────────────────────────────────────────────────────────────────────────────
# Default Attack Parameters
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_SEARCH_RADIUS_M = 50        # meters — spatial tolerance for GPS matching
DEFAULT_TIME_WINDOW_MIN = 5         # minutes — temporal tolerance for timestamp matching

# ──────────────────────────────────────────────────────────────────────────────
# NYC Land Bounding Boxes (to avoid generating trips in the water)
# ──────────────────────────────────────────────────────────────────────────────

NYC_LAND_BOUNDS = [
    # Manhattan
    {"lat_min": 40.7000, "lat_max": 40.8000, "lon_min": -74.0100, "lon_max": -73.9300},
    # Brooklyn/Queens
    {"lat_min": 40.6200, "lat_max": 40.7500, "lon_min": -74.0000, "lon_max": -73.8000},
]

# Typical fare range (USD) for synthetic data
FARE_MIN = 5.00
FARE_MAX = 85.00

# Number of synthetic rows to generate
SYNTHETIC_ROW_COUNT = 1000

# ──────────────────────────────────────────────────────────────────────────────
# Target Trip Definitions (Pre-planted for reliable demo)
# These trips simulate "known" public sightings that an attacker would use.
# ──────────────────────────────────────────────────────────────────────────────

TARGET_TRIPS = [
    {
        "label": "Celebrity A — Leaving The Standard Hotel at 2:03 AM",
        "medallion": "5Z42",
        "hack_license": "437289",
        "pickup_datetime": "2014-06-15 02:03:00",
        "dropoff_datetime": "2014-06-15 02:28:00",
        "pickup_lat": 40.7408,
        "pickup_lon": -74.0080,
        "dropoff_lat": 40.7831,    # Upper West Side residential address
        "dropoff_lon": -73.9712,
        "fare_amount": 22.50,
    },
    {
        "label": "Celebrity B — Pickup at JFK Terminal 4",
        "medallion": "3K17",
        "hack_license": "812456",
        "pickup_datetime": "2014-07-22 14:45:00",
        "dropoff_datetime": "2014-07-22 15:38:00",
        "pickup_lat": 40.6413,
        "pickup_lon": -73.7781,
        "dropoff_lat": 40.7580,    # Times Square hotel
        "dropoff_lon": -73.9855,
        "fare_amount": 62.00,
    },
    {
        "label": "Celebrity C — Leaving Madison Square Garden after event",
        "medallion": "7B09",
        "hack_license": "295103",
        "pickup_datetime": "2014-09-10 23:15:00",
        "dropoff_datetime": "2014-09-10 23:42:00",
        "pickup_lat": 40.7505,
        "pickup_lon": -73.9934,
        "dropoff_lat": 40.7282,    # East Village apartment
        "dropoff_lon": -73.9907,
        "fare_amount": 18.75,
    },
    {
        "label": "Target D — Medical Patient leaving Lenox Hill Hospital",
        "medallion": "9C22",
        "hack_license": "551234",
        "pickup_datetime": "2014-10-12 09:15:00",
        "dropoff_datetime": "2014-10-12 09:40:00",
        "pickup_lat": 40.7725,     # Lenox Hill Hospital
        "pickup_lon": -73.9600,
        "dropoff_lat": 40.6900,    # Brooklyn Heights residence
        "dropoff_lon": -73.9950,
        "fare_amount": 34.50,
    },
]
