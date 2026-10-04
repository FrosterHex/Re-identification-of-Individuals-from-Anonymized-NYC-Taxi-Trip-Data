"""
attack_logic.py — Core Re-identification Attack Engine

Implements the three-phase linkage attack demonstrated by Tockar (2014):

  Phase 1 — Spatial-Temporal Filtering:
      Given "auxiliary knowledge" (a target GPS coordinate + time window),
      filter the anonymized dataset to isolate candidate trips.

  Phase 2 — MD5 Hash Reversal (Rainbow Table Simulation):
      Precompute MD5 hashes for all plausible medallion numbers and hack
      licenses, then reverse-lookup the hash of the isolated trip to
      recover the plaintext identifier.

  Phase 3 — Destination Extraction:
      With the trip uniquely identified, extract the drop-off coordinates
      and fare — information the passenger assumed was protected.

References:
    Tockar, A. (2014). Riding with the stars: Passenger privacy in the NYC
        taxicab dataset. Neustar Research.
    Green, B., et al. (2017). Open data privacy. Berkman Klein Center for
        Internet & Society.
"""

import hashlib
import sys
import time
from math import asin, cos, radians, sin, sqrt

import pandas as pd

from config import (
    DEFAULT_SEARCH_RADIUS_M,
    DEFAULT_TIME_WINDOW_MIN,
    HACK_LICENSE_MAX,
    HACK_LICENSE_MIN,
    MEDALLION_DIGITS,
    MEDALLION_LETTERS,
)


# ──────────────────────────────────────────────────────────────────────────────
# Phase 1 — Spatial-Temporal Filtering
# ──────────────────────────────────────────────────────────────────────────────

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute the great-circle distance in **meters** between two GPS points.

    Uses the Haversine formula. Accurate enough for short urban distances.
    """
    R = 6_371_000  # Earth's radius in meters
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


def filter_by_location(df: pd.DataFrame,
                       target_lat: float,
                       target_lon: float,
                       radius_m: float = DEFAULT_SEARCH_RADIUS_M
                       ) -> pd.DataFrame:
    """Filter trips whose pickup coordinates fall within `radius_m` meters
    of the target (lat, lon).

    Parameters
    ----------
    df : pd.DataFrame
        The full anonymized dataset.
    target_lat, target_lon : float
        The GPS coordinates of the known pickup location.
    radius_m : float
        Search radius in meters.

    Returns
    -------
    pd.DataFrame
        Subset of matching rows with an added `distance_m` column.
    """
    distances = df.apply(
        lambda row: haversine_m(
            target_lat, target_lon,
            row["pickup_latitude"], row["pickup_longitude"]
        ),
        axis=1,
    )
    mask = distances <= radius_m
    result = df.loc[mask].copy()
    result["distance_m"] = distances[mask].round(2)
    return result


def filter_by_time(df: pd.DataFrame,
                   target_time: str,
                   window_min: int = DEFAULT_TIME_WINDOW_MIN
                   ) -> pd.DataFrame:
    """Filter trips whose pickup timestamp falls within +/- `window_min`
    minutes of the target time.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset (or a pre-filtered subset).
    target_time : str
        Target pickup datetime string, e.g. "2014-06-15 02:03:00".
    window_min : int
        Half-width of the time window in minutes.

    Returns
    -------
    pd.DataFrame
        Subset of matching rows.
    """
    target_dt = pd.Timestamp(target_time)
    pickup_dt = pd.to_datetime(df["pickup_datetime"])
    delta = pd.Timedelta(minutes=window_min)
    mask = (pickup_dt >= target_dt - delta) & (pickup_dt <= target_dt + delta)
    return df.loc[mask].copy()


def filter_trips(df: pd.DataFrame,
                 target_lat: float,
                 target_lon: float,
                 target_time: str,
                 radius_m: float = DEFAULT_SEARCH_RADIUS_M,
                 window_min: int = DEFAULT_TIME_WINDOW_MIN
                 ) -> pd.DataFrame:
    """Combined spatial + temporal filter (Phase 1 of the attack).

    Returns
    -------
    pd.DataFrame
        Candidate trips matching the auxiliary knowledge.
    """
    spatial = filter_by_location(df, target_lat, target_lon, radius_m)
    if spatial.empty:
        return spatial
    result = filter_by_time(spatial, target_time, window_min)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Phase 2 — MD5 Rainbow Table Construction & Hash Reversal
# ──────────────────────────────────────────────────────────────────────────────

def _md5(value: str) -> str:
    """Unsalted MD5 hex-digest."""
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def build_medallion_rainbow_table() -> dict[str, str]:
    """Precompute MD5 -> plaintext for all possible medallion numbers.

    Format: <D><L><D><D>, e.g. "1A01" through "9Z99".
    Total keyspace: 9 * 26 * 9 * 9 = 18,954 entries.

    Returns
    -------
    dict
        Mapping of MD5 hex-digest -> plaintext medallion string.
    """
    table: dict[str, str] = {}
    for d1 in MEDALLION_DIGITS:
        for l1 in MEDALLION_LETTERS:
            for d2 in MEDALLION_DIGITS:
                for d3 in MEDALLION_DIGITS:
                    plain = f"{d1}{l1}{d2}{d3}"
                    table[_md5(plain)] = plain
    return table


def build_hack_license_rainbow_table(
    start: int = HACK_LICENSE_MIN,
    end: int = HACK_LICENSE_MAX,
) -> dict[str, str]:
    """Precompute MD5 -> plaintext for all 6-digit hack license numbers.

    Total keyspace: 900,000 entries. In the real 2014 attack this was
    similarly trivial because the license number format was known.

    Returns
    -------
    dict
        Mapping of MD5 hex-digest -> plaintext hack license string.
    """
    table: dict[str, str] = {}
    for n in range(start, end + 1):
        plain = str(n)
        table[_md5(plain)] = plain
    return table


class RainbowTableCracker:
    """Wraps rainbow table construction and lookup with timing metrics.

    Attributes
    ----------
    medallion_table : dict
        MD5 -> plaintext for medallion numbers.
    hack_license_table : dict
        MD5 -> plaintext for hack license numbers.
    build_time_medallion : float
        Seconds taken to build the medallion table.
    build_time_hack : float
        Seconds taken to build the hack license table.
    """

    def __init__(self, build_hack_table: bool = True):
        # Medallion table (always built — small keyspace)
        t0 = time.perf_counter()
        self.medallion_table = build_medallion_rainbow_table()
        self.build_time_medallion = time.perf_counter() - t0

        # Hack license table (optional — larger keyspace)
        if build_hack_table:
            t0 = time.perf_counter()
            self.hack_license_table = build_hack_license_rainbow_table()
            self.build_time_hack = time.perf_counter() - t0
        else:
            self.hack_license_table = {}
            self.build_time_hack = 0.0

    def crack_medallion(self, md5_hash: str) -> str | None:
        """Look up a medallion MD5 hash. Returns plaintext or None."""
        return self.medallion_table.get(md5_hash)

    def crack_hack_license(self, md5_hash: str) -> str | None:
        """Look up a hack license MD5 hash. Returns plaintext or None."""
        return self.hack_license_table.get(md5_hash)

    @property
    def medallion_keyspace(self) -> int:
        return len(self.medallion_table)

    @property
    def hack_license_keyspace(self) -> int:
        return len(self.hack_license_table)

    def stats(self) -> dict:
        """Return construction metrics as a dictionary."""
        # Rough memory estimation (keys + values)
        med_mem = len(self.medallion_table) * (sys.getsizeof("") + 32 + sys.getsizeof("") + 4)
        hack_mem = len(self.hack_license_table) * (sys.getsizeof("") + 32 + sys.getsizeof("") + 6)
        
        return {
            "medallion_keyspace": self.medallion_keyspace,
            "medallion_build_time_s": round(self.build_time_medallion, 4),
            "hack_license_keyspace": self.hack_license_keyspace,
            "hack_license_build_time_s": round(self.build_time_hack, 4),
            "memory_usage_mb": round((med_mem + hack_mem) / (1024 * 1024), 2)
        }


# ──────────────────────────────────────────────────────────────────────────────
# Phase 3 — Destination Extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_destination(trip_row: pd.Series) -> dict:
    """Extract the drop-off (destination) details from a matched trip.

    Parameters
    ----------
    trip_row : pd.Series
        A single row from the filtered dataframe.

    Returns
    -------
    dict
        Destination coordinates, timestamps, and fare.
    """
    return {
        "dropoff_latitude": trip_row["dropoff_latitude"],
        "dropoff_longitude": trip_row["dropoff_longitude"],
        "dropoff_datetime": trip_row["dropoff_datetime"],
        "pickup_datetime": trip_row["pickup_datetime"],
        "pickup_latitude": trip_row["pickup_latitude"],
        "pickup_longitude": trip_row["pickup_longitude"],
        "fare_amount": trip_row["fare_amount"],
        "medallion_hash": trip_row["medallion_hash"],
        "hack_license_hash": trip_row["hack_license_hash"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Defense Simulation (How to fix it)
# ──────────────────────────────────────────────────────────────────────────────

def apply_spatial_cloaking(df: pd.DataFrame, precision: int = 2) -> pd.DataFrame:
    """Rounds GPS coordinates to simulate K-Anonymity defense.
    
    Rounding to 2 decimal places creates blocks of roughly 1.1km.
    """
    cloaked = df.copy()
    cloaked["pickup_latitude"] = cloaked["pickup_latitude"].round(precision)
    cloaked["pickup_longitude"] = cloaked["pickup_longitude"].round(precision)
    return cloaked


# ──────────────────────────────────────────────────────────────────────────────
# Full Attack Pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run_attack(df: pd.DataFrame,
               target_lat: float,
               target_lon: float,
               target_time: str,
               radius_m: float = DEFAULT_SEARCH_RADIUS_M,
               window_min: int = DEFAULT_TIME_WINDOW_MIN,
               crack_hack_license: bool = True,
               cloak_precision: int | None = None,
               is_salted: bool = False,
               ) -> dict:
    """Execute the full three-phase re-identification attack.

    Parameters
    ----------
    df : pd.DataFrame
        The anonymized taxi dataset.
    target_lat, target_lon : float
        Known pickup GPS coordinates (auxiliary knowledge).
    target_time : str
        Known pickup time (auxiliary knowledge).
    radius_m : float
        Spatial search radius in meters.
    window_min : int
        Temporal search half-window in minutes.
    crack_hack_license : bool
        Whether to also crack the hack license hash (slower).
    cloak_precision : int | None
        If set, simulate spatial cloaking by rounding GPS to this precision.
    is_salted : bool
        If True, simulates that hashes were properly salted (attack fails).

    Returns
    -------
    dict
        Complete attack results including matched trips, cracked hashes,
        destination details, and performance metrics.
    """
    results: dict = {
        "success": False,
        "phase1_candidates": 0,
        "matched_trips": None,
        "cracked_medallion": None,
        "cracked_hack_license": None,
        "destination": None,
        "rainbow_table_stats": None,
        "attack_params": {
            "target_lat": target_lat,
            "target_lon": target_lon,
            "target_time": target_time,
            "radius_m": radius_m,
            "window_min": window_min,
        },
    }

    # --- Phase 1: Filter ---
    # Apply defense if enabled
    if cloak_precision is not None:
        df = apply_spatial_cloaking(df, cloak_precision)
        # We must also apply it to the attacker's knowledge to match
        target_lat = round(target_lat, cloak_precision)
        target_lon = round(target_lon, cloak_precision)

    t_start = time.perf_counter()
    candidates = filter_trips(df, target_lat, target_lon, target_time,
                              radius_m, window_min)
    results["phase1_time_s"] = round(time.perf_counter() - t_start, 4)
    results["phase1_candidates"] = len(candidates)
    results["matched_trips"] = candidates

    if candidates.empty:
        return results

    # Take the closest match
    if "distance_m" in candidates.columns:
        best = candidates.sort_values("distance_m").iloc[0]
    else:
        best = candidates.iloc[0]

    # --- Phase 2: Crack hashes ---
    if is_salted:
        # Simulate salted hash defense (impossible to build rainbow table in reasonable time)
        results["rainbow_table_stats"] = {
            "medallion_keyspace": "∞ (Salted)",
            "medallion_build_time_s": "∞",
            "hack_license_keyspace": "∞",
            "hack_license_build_time_s": "∞",
            "memory_usage_mb": 0.0
        }
        results["cracked_medallion"] = "[PROTECTED]"
        results["cracked_hack_license"] = "[PROTECTED]"
        results["phase2_time_s"] = 0.0
    else:
        cracker = RainbowTableCracker(build_hack_table=crack_hack_license)
        results["rainbow_table_stats"] = cracker.stats()

        t_start = time.perf_counter()
        results["cracked_medallion"] = cracker.crack_medallion(
            best["medallion_hash"]
        )
        if crack_hack_license:
            results["cracked_hack_license"] = cracker.crack_hack_license(
                best["hack_license_hash"]
            )
        results["phase2_time_s"] = round(time.perf_counter() - t_start, 6)

    # --- Phase 3: Extract destination ---
    results["destination"] = extract_destination(best)
    results["success"] = True

    return results
