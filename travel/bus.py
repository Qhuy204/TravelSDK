"""
Bus search module for TravelSDK.
Wraps /v2/route endpoint for bus tickets.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

from travel.constants import BUS_SEARCH_URL, BUS_COUNT_URL, PROVIDER_BASE_URL
from travel.models import BusTicket, Provider, PointInfo

if TYPE_CHECKING:
    from travel.client import TravelClient

logger = logging.getLogger(__name__)


def _time_id() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _parse_bus(raw: dict, from_id: int, to_id: int) -> BusTicket:
    """Parse a raw bus result into a BusTicket model."""
    company_raw = raw.get("company", {})
    operator = Provider(
        code=company_raw.get("code", ""),
        name=company_raw.get("name") or raw.get("busName", ""),
    )
    
    rating = 0.0
    reviews = 0
    ratings_raw = company_raw.get("ratings", {})
    if isinstance(ratings_raw, dict):
        rating = float(ratings_raw.get("overall", 0.0))
        reviews = int(ratings_raw.get("comments", 0))


    price = 0
    final_price = 0
    route_obj = raw.get("route", {})
    if isinstance(route_obj, dict):
        schedules = route_obj.get("schedules", [])
        if schedules and isinstance(schedules, list):
            fare = schedules[0].get("fare", {})
            if isinstance(fare, dict):
                price = int(fare.get("discount", 0) or fare.get("original", 0))
                final_price = int(fare.get("original", 0) or price)

    if not price:
        price = int(raw.get("fareLarge") or raw.get("price") or raw.get("fare") or 0)
    if not final_price:
        final_price = int(raw.get("originalFare") or raw.get("fareSmall") or raw.get("finalPrice") or raw.get("total_price") or price)

    bus_type = ""
    utilities = []
    policies = []
    promotions = []
    
    pickup_points = []
    dropoff_points = []
    seat_avail = 0
    
    if str(raw.get("speaking_english_utility", "")).lower() == "true":
        utilities.append("Nhân viên nói Tiếng Anh")
        
    # Coupons / promotions at root level
    for coup in raw.get("coupons", []):
        if isinstance(coup, dict) and coup.get("campaign_name"):
            promotions.append(coup.get("campaign_name"))
        
    if isinstance(route_obj, dict):
        for pt in route_obj.get("pickup_points", []):
            loc = pt.get("location", {})
            pickup_points.append(PointInfo(
                name=pt.get("name", ""),
                address=pt.get("address", ""),
                time_offset_minutes=pt.get("duration", 0),
                lat=loc.get("lat", 0.0),
                lon=loc.get("lon", 0.0)
            ))
            
        for pt in route_obj.get("dropoff_points", []):
            loc = pt.get("location", {})
            dropoff_points.append(PointInfo(
                name=pt.get("name", ""),
                address=pt.get("address", ""),
                time_offset_minutes=pt.get("duration", 0),
                lat=loc.get("lat", 0.0),
                lon=loc.get("lon", 0.0)
            ))
            
        schedules = route_obj.get("schedules", [])
        if schedules and isinstance(schedules, list):
            sch = schedules[0]
            if isinstance(sch, dict):
                bus_type = sch.get("vehicle_type") or sch.get("seat_template_name", "")
                seat_avail = sch.get("available_seats", sch.get("total_available_seats", 0))
                
                # Sometime fill_rate or other logics apply, but prefer explicit available_seats
                if str(sch.get("refundable")) == "1":
                    policies.append("Có thể hoàn hủy vé")
                if sch.get("config") == "ONLINE":
                    policies.append("Có thể thanh toán online")

    # Duration: can be '34h' or float/int hours or minutes
    duration_val = raw.get("duration", 0)
    duration_mins = 0
    if isinstance(duration_val, str) and duration_val.endswith("h"):
        try:
            duration_mins = int(float(duration_val[:-1]) * 60)
        except Exception:
            pass
    elif isinstance(duration_val, (int, float)):
        duration_mins = int(duration_val)

    from_slug = raw.get("from_slug", "")
    to_slug = raw.get("to_slug", "")
    dep_date = raw.get("departure_date", raw.get("departureDate", raw.get("date", "")))
    if dep_date and "T" in dep_date:
        dep_date = dep_date.split("T")[0]

    # Time fields Extraction
    dep_time = raw.get("fromTime", raw.get("time", raw.get("departureTime", "")))
    arr_time = raw.get("toTime", raw.get("arrivalTime", ""))
    
    if route_obj and isinstance(route_obj, dict):
        if not dep_time:
            dep_time = route_obj.get("departure_time", "")
        # Arrival time is sometimes buried deep in schedules
        if not arr_time:
            schedules = route_obj.get("schedules", [])
            if schedules and isinstance(schedules, list):
                arr_time_str = schedules[0].get("arrival_time", "")
                # arrival_time might be like "2026-04-21T07:00+07:00", simplify to "07:00"
                if "T" in arr_time_str:
                    arr_time = arr_time_str.split("T")[1][:5]
                else:
                    arr_time = arr_time_str

    # Override seat available if found in top level
    top_seat = raw.get("numberSeatAvailable", raw.get("seat_available", raw.get("seatAvailable")))
    if top_seat is not None:
        seat_avail = top_seat

    # Images from company
    images = []
    if isinstance(company_raw, dict):
        for img in company_raw.get("images", []):
            if isinstance(img, dict) and img.get("files"):
                url = img["files"].get("1000x600") or img["files"].get("600x350")
                if url:
                    if url.startswith("//"): url = "https:" + url
                    images.append(url)

    return BusTicket(
        id_index=raw.get("idIndex", raw.get("id", "")),
        session_id=raw.get("session", ""),
        operator=operator,
        from_id=from_id,
        to_id=to_id,
        from_name=raw.get("fromName", raw.get("from", raw.get("departureName", ""))),
        to_name=raw.get("toName", raw.get("to", raw.get("arrivalName", ""))),
        departure_date=dep_date,
        departure_time=dep_time,
        arrival_time=arr_time,
        duration_minutes=duration_mins,
        seat_available=seat_avail,
        bus_type=bus_type or raw.get("vehicleTypeStr", raw.get("busType", raw.get("type", ""))),
        pickup_points=pickup_points,
        dropoff_points=dropoff_points,
        price=price,
        final_price=final_price,
        utilities=utilities,
        policies=policies,
        promotions=promotions,
        rating=rating,
        reviews=reviews,
        images=images,
        raw=raw,
    )


async def search_buses(
    client: "TravelClient",
    from_id: int,
    to_id: int,
    date: str,
    passengers: int = 1,
    page: int = 1,
    page_size: int = 20,
    sort: str = "fare:asc",
) -> list[BusTicket]:
    """
    Search for bus tickets.
    
    Args:
        client: TravelClient instance.
        from_id: Origin city region ID (e.g., 124 for Hà Nội).
        to_id: Destination city region ID (e.g., 1291 for Sài Gòn).
        date: Travel date in "YYYY-MM-DD" format.
        passengers: Number of passengers (default: 1).
        page: Result page (default: 1).
        page_size: Results per page (default: 20).
        sort: Sort order (default: "fare:asc").
    
    Returns:
        List of BusTicket objects.
    
    Note:
        Bus region IDs can be found using locations.resolve_bus_region().
        Common IDs: Hà Nội=124, Sài Gòn=1291, Đà Nẵng=174.
    """
    tid = _time_id()
    params = {
        "filter[from][0]": from_id,
        "filter[to][0]": to_id,
        "filter[date]": date,
        "filter[quantity]": passengers,
        "filter[page]": page,
        "filter[pagesize]": page_size,
        "filter[time_id]": tid,
        "page": page,
        "pagesize": page_size,
        "sort": sort,
        "time_id": tid,
        "v": 9,
    }

    logger.debug(f"Searching buses: region {from_id} -> {to_id} on {date}")

    try:
        data = await client._get(BUS_SEARCH_URL, params=params)
    except httpx.HTTPStatusError as e:
        logger.error(f"Bus search failed: {e}")
        return []

    if data.get("message") != "success":
        logger.warning(f"Bus search returned non-success: {data.get('message')}")
        return []

    tickets = []
    for item in data.get("data", []):
        try:
            tickets.append(_parse_bus(item, from_id, to_id))
        except Exception as e:
            logger.warning(f"Failed to parse bus item: {e}")

    logger.info(f"Found {len(tickets)} buses from region {from_id} to {to_id} on {date}")
    return tickets


async def get_bus_calendar(
    client: "TravelClient",
    from_id: int,
    to_id: int,
    month: int,
    year: int,
    passengers: int = 1,
) -> dict:
    """Get bus availability calendar for a given month."""
    tid = _time_id()
    params = {
        "filter[from][0]": from_id,
        "filter[to][0]": to_id,
        "filter[month_years][0]": f"{month}-{year}",
        "filter[quantity]": passengers,
        "page": 1,
        "time_id": tid,
    }

    try:
        data = await client._get(BUS_COUNT_URL, params=params)
    except httpx.HTTPStatusError as e:
        logger.error(f"Bus calendar failed: {e}")
        return {}

    return data
