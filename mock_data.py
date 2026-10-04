"""
mock_data.py — Synthetic NYC Yellow Taxi Trip Data Generator (2014 FOIL Simulation)

Generates a CSV file (`taxi_data_2014.csv`) containing ~1,000 synthetic taxi trip
records that mirror the schema of the real 2014 NYC TLC FOIL release. The key
vulnerability is replicated: medallion numbers and hack license numbers are
hashed with unsalted MD5, while precise GPS coordinates and timestamps remain
in the clear.

Three "target" trips are planted at known NYC landmarks with specific timestamps
so the linkage attack can succeed reliably in the demonstration.

Usage:
    python mock_data.py

Output:
    taxi_data_2014.csv  — 1,000-row synthetic dataset

References:
    Tockar, A. (2014). Riding with the stars: Passenger privacy in the NYC
        taxicab dataset. Neustar Research.
    Green, B., et al. (2017). Open data privacy. Berkman Klein Center for
        Internet & Society.
"""

import csv
import hashlib
import math
import os
import random
from datetime import datetime, timedelta

from config import (
    FARE_MAX,
    FARE_MIN,
    HACK_LICENSE_MAX,
    HACK_LICENSE_MIN,
    MEDALLION_DIGITS,
    MEDALLION_LETTERS,
    NYC_LAND_BOUNDS,
    SYNTHETIC_ROW_COUNT,
    TARGET_TRIPS,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def md5_hash(value: str) -> str:
    """Return the hex-digest MD5 hash of a plain-text string.

    This replicates the exact (flawed) anonymization method used by the NYC TLC
    in 2014: `hashlib.md5(value.encode()).hexdigest()` with NO salt.
    """
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def random_medallion() -> str:
    """Generate a random NYC taxi medallion in the format <D><L><D><D>.

    Example: '5Z42', '3K17'
    """
    d1 = random.choice(MEDALLION_DIGITS)
    l1 = random.choice(MEDALLION_LETTERS)
    d2 = random.choice(MEDALLION_DIGITS)
    d3 = random.choice(MEDALLION_DIGITS)
    return f"{d1}{l1}{d2}{d3}"


def random_hack_license() -> str:
    """Generate a random 6-digit hack license number as a string."""
    return str(random.randint(HACK_LICENSE_MIN, HACK_LICENSE_MAX))


def random_coordinate(lat_min: float, lat_max: float,
                       lon_min: float, lon_max: float) -> tuple[float, float]:
    """Return a random (latitude, longitude) within the given bounding box."""
    lat = round(random.uniform(lat_min, lat_max), 6)
    lon = round(random.uniform(lon_min, lon_max), 6)
    return lat, lon


def random_datetime_2014() -> datetime:
    """Return a random datetime in the year 2014."""
    start = datetime(2014, 1, 1)
    end = datetime(2014, 12, 31, 23, 59, 59)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def random_trip_duration() -> timedelta:
    """Return a random trip duration between 3 and 60 minutes."""
    return timedelta(minutes=random.randint(3, 60))


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in miles between two coordinates."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))


# ──────────────────────────────────────────────────────────────────────────────
# Row Builders
# ──────────────────────────────────────────────────────────────────────────────

def build_random_row() -> dict:
    """Build a single random (non-target) trip record."""
    medallion = random_medallion()
    hack_license = random_hack_license()
    pickup_dt = random_datetime_2014()
    dropoff_dt = pickup_dt + random_trip_duration()
    
    pickup_bounds = random.choice(NYC_LAND_BOUNDS)
    dropoff_bounds = random.choice(NYC_LAND_BOUNDS)
    
    pickup_lat, pickup_lon = random_coordinate(**pickup_bounds)
    dropoff_lat, dropoff_lon = random_coordinate(**dropoff_bounds)
    
    # Calculate realistic fare: $2.50 base + $2.50 per mile + random variation
    distance_miles = haversine_miles(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
    fare = round(2.50 + (2.50 * distance_miles) + random.uniform(0.5, 3.0), 2)

    return {
        "medallion_hash": md5_hash(medallion),
        "hack_license_hash": md5_hash(hack_license),
        "pickup_datetime": pickup_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "dropoff_datetime": dropoff_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_longitude": pickup_lon,
        "pickup_latitude": pickup_lat,
        "dropoff_longitude": dropoff_lon,
        "dropoff_latitude": dropoff_lat,
        "fare_amount": fare,
    }


def build_target_row(trip: dict) -> dict:
    """Build a row from a pre-defined target trip specification."""
    return {
        "medallion_hash": md5_hash(trip["medallion"]),
        "hack_license_hash": md5_hash(trip["hack_license"]),
        "pickup_datetime": trip["pickup_datetime"],
        "dropoff_datetime": trip["dropoff_datetime"],
        "pickup_longitude": trip["pickup_lon"],
        "pickup_latitude": trip["pickup_lat"],
        "dropoff_longitude": trip["dropoff_lon"],
        "dropoff_latitude": trip["dropoff_lat"],
        "fare_amount": trip["fare_amount"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main Generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_dataset(output_path: str = "taxi_data_2014.csv",
                     n_rows: int = SYNTHETIC_ROW_COUNT) -> str:
    """Generate the synthetic taxi dataset and write it to CSV.

    Parameters
    ----------
    output_path : str
        File path for the output CSV.
    n_rows : int
        Total number of rows (including target trips).

    Returns
    -------
    str
        Absolute path to the generated CSV file.
    """
    random.seed(42)  # Reproducibility

    fieldnames = [
        "medallion_hash",
        "hack_license_hash",
        "pickup_datetime",
        "dropoff_datetime",
        "pickup_longitude",
        "pickup_latitude",
        "dropoff_longitude",
        "dropoff_latitude",
        "fare_amount",
    ]

    rows: list[dict] = []

    # --- Insert target trips first ---
    for trip in TARGET_TRIPS:
        rows.append(build_target_row(trip))
        print(f"  [TARGET] Planted: {trip['label']}")
        print(f"           Medallion '{trip['medallion']}' -> MD5: {md5_hash(trip['medallion'])}")

    # --- Fill remaining rows with random data ---
    n_random = n_rows - len(TARGET_TRIPS)
    for _ in range(n_random):
        rows.append(build_random_row())

    # --- Shuffle so targets are not at the top ---
    random.shuffle(rows)

    # --- Write CSV ---
    abs_path = os.path.abspath(output_path)
    with open(abs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[OK] Generated {len(rows)} rows -> {abs_path}")
    return abs_path


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    generate_dataset()
