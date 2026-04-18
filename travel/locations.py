"""
Location utilities for TravelSDK.
Resolves and normalizes city/station names to Travel IDs.
"""

from __future__ import annotations

import difflib
import logging
from typing import Optional

from travel.constants import (
    TRAIN_STATIONS,
    TRAIN_CODE_TO_INFO,
    FLIGHT_AIRPORTS,
    BUS_REGIONS,
)

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return text.lower().strip()


def resolve_train_station(query: str) -> Optional[dict]:
    """
    Resolve a city name or station code to its train station info.
    
    Args:
        query: City name (e.g., "Hà Nội", "hanoi"), or code (e.g., "HNO")
    
    Returns:
        Station info dict with 'code', 'name', 'location_id' etc., or None.
    
    Example:
        >>> resolve_train_station("Hà Nội")
        {'code': 'HNO', 'name': 'Hà Nội', 'location_id': 102188, ...}
    """
    q = _normalize(query)
    
    # Direct code match (e.g., "HNO")
    if query.upper() in TRAIN_CODE_TO_INFO:
        return TRAIN_CODE_TO_INFO[query.upper()]
    
    # Direct key match (e.g., "hanoi")
    if q in TRAIN_STATIONS:
        return TRAIN_STATIONS[q]
    
    # Search by alias
    for key, info in TRAIN_STATIONS.items():
        if q in [_normalize(a) for a in info.get("aliases", [])]:
            return info
        if q == _normalize(info["name"]):
            return info
    
    # Fuzzy match
    all_names = list(TRAIN_STATIONS.keys()) + [
        _normalize(a)
        for info in TRAIN_STATIONS.values()
        for a in info.get("aliases", [])
    ]
    matches = difflib.get_close_matches(q, all_names, n=1, cutoff=0.6)
    if matches:
        matched = matches[0]
        for key, info in TRAIN_STATIONS.items():
            if _normalize(key) == matched or matched in [_normalize(a) for a in info.get("aliases", [])]:
                logger.info(f"Fuzzy matched '{query}' -> '{info['name']}'")
                return info
    
    logger.warning(f"Could not resolve train station: '{query}'")
    return None


def resolve_flight_airport(query: str) -> Optional[dict]:
    """
    Resolve a city name or IATA code to its airport info.
    
    Args:
        query: IATA code (e.g., "HAN") or city name (e.g., "Hà Nội")
    
    Returns:
        Airport info dict with 'iata', 'city', 'name', 'region_id', etc.
    """
    q = _normalize(query)
    
    # Direct IATA code match
    if query.upper() in FLIGHT_AIRPORTS:
        info = FLIGHT_AIRPORTS[query.upper()].copy()
        info["iata"] = query.upper()
        return info
    
    # Search by alias or city name
    for iata, info in FLIGHT_AIRPORTS.items():
        aliases = [_normalize(a) for a in info.get("aliases", [])]
        if q in aliases or q == _normalize(info["city"]) or q == _normalize(info["name"]):
            result = info.copy()
            result["iata"] = iata
            return result
    
    # Fuzzy match
    candidates = {iata: _normalize(info["city"]) for iata, info in FLIGHT_AIRPORTS.items()}
    matches = difflib.get_close_matches(q, list(candidates.values()), n=1, cutoff=0.6)
    if matches:
        for iata, city in candidates.items():
            if city == matches[0]:
                logger.info(f"Fuzzy matched '{query}' -> '{iata}'")
                result = FLIGHT_AIRPORTS[iata].copy()
                result["iata"] = iata
                return result
    
    logger.warning(f"Could not resolve flight airport: '{query}'")
    return None


def resolve_bus_region(query: str) -> Optional[dict]:
    """
    Resolve a city name to its bus region ID.
    
    Args:
        query: City name (e.g., "Hà Nội") or region key (e.g., "hanoi")
    
    Returns:
        Region info dict with 'id', 'name', 'slug', etc.
    """
    q = _normalize(query)
    
    # Direct key match
    if q in BUS_REGIONS:
        return BUS_REGIONS[q]
    
    # Search by alias or name
    for key, info in BUS_REGIONS.items():
        aliases = [_normalize(a) for a in info.get("aliases", [])]
        if q in aliases or q == _normalize(info["name"]):
            return info
    
    # Fuzzy match
    all_names = list(BUS_REGIONS.keys()) + [
        _normalize(a)
        for info in BUS_REGIONS.values()
        for a in info.get("aliases", [])
    ]
    matches = difflib.get_close_matches(q, all_names, n=1, cutoff=0.6)
    if matches:
        matched = matches[0]
        for key, info in BUS_REGIONS.items():
            if _normalize(key) == matched or matched in [_normalize(a) for a in info.get("aliases", [])]:
                logger.info(f"Fuzzy matched '{query}' -> '{info['name']}'")
                return info
    
    logger.warning(f"Could not resolve bus region: '{query}'")
    return None
