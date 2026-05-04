"""Great-circle distance helpers.

Pure maths, no network, no DB. The matcher uses `haversine_km` to turn two
lat/lng pairs into a scalar that slots into the location scorer. Kept as a
standalone module so scrapers, scorer and API can all reuse it.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points, in kilometres."""
    p1 = radians(lat1)
    p2 = radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def distance_score(distance_km: float, soft_km: float = 30.0, hard_km: float = 80.0) -> float:
    """Map a distance (km) to a score in [0, 1].

    - ≤ soft_km  → 1.0   (same city / neighbour town, perfect)
    - ≥ hard_km  → 0.0   (too far for a student job)
    - in between → linear decay

    Defaults tuned for France: a student job is acceptable up to ~80 km, best
    under 30 km (typical commute).
    """
    if distance_km <= soft_km:
        return 1.0
    if distance_km >= hard_km:
        return 0.0
    return round(1.0 - (distance_km - soft_km) / (hard_km - soft_km), 4)
