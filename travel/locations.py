import asyncio
import difflib
import json
import logging
import os
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from travel.client import TravelClient

from travel.constants import (
    TRAIN_STATIONS,
    TRAIN_CODE_TO_INFO,
    FLIGHT_AIRPORTS,
    BUS_REGIONS,
)

logger = logging.getLogger(__name__)

# Load the local location database
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_DB_PATH = os.path.join(_DATA_DIR, "all_locations.json")
_LOCATIONS_DB = {"provinces": [], "districts": [], "airports": [], "train_stations": []}

try:
    if os.path.exists(_DB_PATH):
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            _LOCATIONS_DB = json.load(f)
        logger.debug(f"Loaded {len(_LOCATIONS_DB['provinces'])} provinces from local database.")
except Exception as e:
    logger.warning(f"Could not load local locations database: {e}")


def _normalize(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return text.lower().strip()


def get_all_provinces() -> List[dict]:
    """Return a list of all 63 provinces in Vietnam."""
    return _LOCATIONS_DB.get("provinces", [])


def get_all_airports() -> List[dict]:
    """Return a list of all airports in Vietnam."""
    return _LOCATIONS_DB.get("airports", [])


def get_all_train_stations() -> List[dict]:
    """Return a list of all train stations in Vietnam."""
    return _LOCATIONS_DB.get("train_stations", [])


def resolve_train_station(query: str) -> Optional[dict]:
    """
    Resolve a city name or station code to its train station info.
    
    Args:
        query: City name (e.g., "Hà Nội", "hanoi"), or code (e.g., "HNO")
    """
    q = _normalize(query)
    
    # Check Code match in existing constants
    if query.upper() in TRAIN_CODE_TO_INFO:
        return TRAIN_CODE_TO_INFO[query.upper()]
    
    # Check local DB for code match
    for s in _LOCATIONS_DB.get("train_stations", []):
        if s["code"].upper() == query.upper():
            return {
                "code": s["code"],
                "name": s["name"],
                "location_id": s["id"],
                "region_id": s.get("province_id")
            }

    # Direct key match in constants
    if q in TRAIN_STATIONS:
        return TRAIN_STATIONS[q]
    
    # Fuzzy match logic simplified for now
    for key, info in TRAIN_STATIONS.items():
        if q == _normalize(info["name"]):
            return info
            
    return None


def resolve_flight_airport(query: str) -> Optional[dict]:
    """Resolve a city name or IATA code to its airport info."""
    q = _normalize(query)
    
    # Direct IATA match in constants
    if query.upper() in FLIGHT_AIRPORTS:
        info = FLIGHT_AIRPORTS[query.upper()].copy()
        info["iata"] = query.upper()
        return info
        
    # Check local DB for IATA match
    for a in _LOCATIONS_DB.get("airports", []):
        if a.get("iata") == query.upper():
            return {
                "iata": a["iata"],
                "name": a["name"],
                "city": a.get("city"),
                "region_id": a.get("province_id")
            }
            
    # Search by city name
    for iata, info in FLIGHT_AIRPORTS.items():
        if q == _normalize(info["city"]) or q == _normalize(info["name"]):
            result = info.copy()
            result["iata"] = iata
            return result
            
    return None


def resolve_bus_region(query: str) -> Optional[dict]:
    """Resolve a city name to its bus region ID."""
    q = _normalize(query)
    
    # Check constants
    if q in BUS_REGIONS:
        return BUS_REGIONS[q]
        
    # Check local DB for province match
    for p in _LOCATIONS_DB.get("provinces", []):
        if _normalize(p["name"]) == q:
            return {
                "id": int(p["id"]),
                "name": p["name"],
                "slug": p.get("code", "").lower() or q
            }
            
    return None


async def resolve_location_async(query: str, client: "TravelClient", recursive_hubs: bool = True) -> Optional[dict]:
    """
    Dynamically resolve a location name by searching via Travel API.
    Supports hierarchical resolution for hub searching (District -> Province).
    """
    areas = await client.search_areas(query)
    if not areas:
        return None
        
    q_norm = query.lower().strip()
    
    # Sort areas by relevance
    best_area = None
    for area in areas:
        name_norm = area.get("name", "").lower().strip()
        if name_norm == q_norm:
            if str(area.get("type")) == "3": # Province
                best_area = area
                break
            if not best_area:
                best_area = area
    
    if not best_area:
        # Prioritize Province (3) then District (5)
        for t in ["3", "5"]:
            for area in areas:
                if str(area.get("type")) == t:
                    best_area = area
                    break
            if best_area: break
            
    if not best_area:
        best_area = areas[0]
        
    # If we need detail metadata but it's missing hubs, fetch details recursively
    if recursive_hubs:
        has_hubs = best_area.get("airports") or best_area.get("train_stations")
        if not has_hubs and best_area.get("state_id"):
            logger.info(f"Area {best_area['name']} (ID: {best_area['id']}) has no hubs. Fetching parent province ID {best_area['state_id']}...")
            parent_details = await client.get_area_details(best_area["state_id"])
            if parent_details:
                # Merge hubs from parent into the result
                best_area["airports"] = parent_details.get("airports", [])
                best_area["train_stations"] = parent_details.get("train_stations", [])
                best_area["parent_id"] = best_area["state_id"]
                
    return best_area


async def resolve_bus_region_async(query: str, client: "TravelClient") -> Optional[dict]:
    """Async version of resolve_bus_region with dynamic search fallback."""
    info = resolve_bus_region(query)
    if info:
        return info
        
    area = await resolve_location_async(query, client, recursive_hubs=False)
    if area:
        return {
            "id": int(area["id"]),
            "name": area["name"],
            "slug": area.get("code", "").lower() or query,
            "dynamic": True
        }
        
    return None


async def resolve_train_station_async(query: str, client: "TravelClient") -> Optional[dict]:
    """Async version with recursive hub resolution to find nearest provincial station."""
    info = resolve_train_station(query)
    if info:
        return info
        
    area = await resolve_location_async(query, client, recursive_hubs=True)
    if area and area.get("train_stations"):
        station = area["train_stations"][0]
        logger.info(f"Resolved train station: {station['name']} (via {area['name']})")
        return {
            "code": station["code"],
            "name": station["name"],
            "location_id": station["id"],
            "region_id": int(area.get("parent_id") or area["id"]),
            "dynamic": True
        }
        
    return None


async def resolve_flight_airport_async(query: str, client: "TravelClient") -> Optional[dict]:
    """Async version with recursive hub resolution to find nearest provincial airport."""
    info = resolve_flight_airport(query)
    if info:
        return info
        
    area = await resolve_location_async(query, client, recursive_hubs=True)
    if area and area.get("airports"):
        airport_feat = area["airports"][0]
        props = airport_feat.get("properties", {})
        logger.info(f"Resolved airport: {props.get('AirportName_Vi')} (via {area['name']})")
        return {
            "iata": props.get("IATA_FAA") or props.get("ICAO"),
            "city": props.get("CityName_Vi"),
            "name": props.get("AirportName_Vi") or props.get("NAME"),
            "region_id": int(area.get("parent_id") or area["id"]),
            "location_id": props.get("VxrAreaId"),
            "dynamic": True
        }
        
    return None
