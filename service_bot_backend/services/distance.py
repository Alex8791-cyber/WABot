"""Geocoding and distance calculation using Nominatim + Haversine."""

import math
import logging
from typing import Dict, Any, Optional, Tuple

import httpx

import config as cfg

logger = logging.getLogger("service_bot")

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "WABot/1.0"


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two points using Haversine formula."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geocode(address: str) -> Optional[Tuple[float, float]]:
    """Geocode an address to (lat, lng) using Nominatim."""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(_NOMINATIM_URL, params={
                "q": address,
                "format": "json",
                "limit": 1,
            }, headers={"User-Agent": _USER_AGENT})
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        logger.error("Geocoding failed for '%s': %s", address, e)
    return None


def get_business_location() -> Optional[Tuple[float, float]]:
    """Get the business location. Returns (lat, lng) or None if not configured."""
    if cfg.BUSINESS_LAT and cfg.BUSINESS_LNG:
        return cfg.BUSINESS_LAT, cfg.BUSINESS_LNG
    if cfg.BUSINESS_ADDRESS:
        coords = geocode(cfg.BUSINESS_ADDRESS)
        if coords:
            # Cache in config for subsequent calls
            cfg.BUSINESS_LAT, cfg.BUSINESS_LNG = coords
            return coords
    return None


def calculate_distance(customer_address: str) -> Dict[str, Any]:
    """Calculate distance from business to customer address.

    Returns dict with distance_km, business_address, customer_address,
    or an error message.
    """
    business = get_business_location()
    if not business:
        return {"error": "Business location not configured. Set BUSINESS_ADDRESS or BUSINESS_LAT/BUSINESS_LNG."}

    customer_coords = geocode(customer_address)
    if not customer_coords:
        return {"error": f"Could not find location for: {customer_address}"}

    distance = _haversine(business[0], business[1], customer_coords[0], customer_coords[1])

    return {
        "distance_km": round(distance, 1),
        "business_location": {
            "lat": business[0],
            "lng": business[1],
            "address": cfg.BUSINESS_ADDRESS or f"{business[0]}, {business[1]}",
        },
        "customer_location": {
            "lat": customer_coords[0],
            "lng": customer_coords[1],
            "address": customer_address,
        },
    }
