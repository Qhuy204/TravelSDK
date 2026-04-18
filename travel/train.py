"""
Train search module for TravelSDK.
Wraps /v2/route/train endpoint.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

import httpx

from travel.constants import (
    TRAIN_SEARCH_URL,
    TRAIN_COUNT_URL,
    PROVIDER_BASE_URL,
    SEAT_CLASS_LABELS,
)
from travel.models import TrainTicket, CarInfo, SeatOption, SeatClass, Provider

if TYPE_CHECKING:
    from travel.client import TravelClient

logger = logging.getLogger(__name__)


def _time_id() -> str:
    """Generate a time_id parameter (current local time as HH:MM:SS)."""
    return datetime.now().strftime("%H:%M:%S")


def _map_seat_class(group_code: str) -> SeatClass:
    mapping = {
        "NGM": SeatClass.SOFT_SEAT,
        "NAC": SeatClass.SLEEPER_6,
        "NAM": SeatClass.SLEEPER_4,
    }
    return mapping.get(group_code, SeatClass.UNKNOWN)


def _parse_car(car_raw: dict, group_fallback: str = "NGM") -> CarInfo:
    """Parse a raw toa_xe object into a CarInfo model."""
    group = car_raw.get("nhom_cho_web", group_fallback)
    seat_class = _map_seat_class(group)

    seat_options: list[SeatOption] = []
    for scs in car_raw.get("seat_class_status", []):
        for code, details in scs.items():
            label = SEAT_CLASS_LABELS.get(code, code)
            seat_options.append(SeatOption(
                code=code,
                label=label,
                seat_class=seat_class,
                price=details.get("price", 0),
                markup_price=details.get("markupPrice"),
                available=details.get("quantity", 0),
            ))

    return CarInfo(
        car_id=car_raw.get("id", 0),
        car_number=car_raw.get("toa_so", "?"),
        car_type=car_raw.get("toa_xe_dien_giai", ""),
        group_code=group,
        total_available=car_raw.get("so_cho_trong", 0),
        seat_options=seat_options,
        min_price=car_raw.get("min_price", 0),
    )


def _parse_train(raw: dict) -> TrainTicket:
    """Parse a raw train result dict into a TrainTicket model."""
    company_raw = raw.get("company", {})
    operator = Provider(
        code=company_raw.get("code", "VNR"),
        name=company_raw.get("name", "Vietnam Railways"),
    )

    # Parse cars
    cars = [_parse_car(car) for car in raw.get("list_toa_xe", [])]

    # Min price from first car or from session data
    min_price = min((c.min_price for c in cars if c.min_price > 0), default=0)

    # Train number from segments or id_index
    train_num = ""
    segs = raw.get("segments", [])
    if segs:
        train_num = segs[0].get("train_number", "")
    if not train_num:
        parts = raw.get("idIndex", "").split("|")
        train_num = parts[1] if len(parts) > 1 else ""

    # Id index
    id_index = raw.get("idIndex", "")
    
    # Utilities: detect from car descriptions
    utilities = []
    unique_types = set(c.car_type for c in cars)
    for ct in unique_types:
        if "điều hòa" in ct.lower():
            utilities.append("Điều hòa")
            break
    if cars:
        utilities.extend(["Ổ cắm điện", "Nhà vệ sinh"]) 
    
    # Policies & Promotions
    policies = []
    promotions = []
    discounts = raw.get("list_discount_display", [])
    if isinstance(discounts, list):
        for d in discounts:
            d_name = d.get("ten_khuyen_mai")
            d_detail = d.get("noi_dung_khuyen_mai_detail")
            if d_name:
                promotions.append(d_name)
            if d_detail:
                # Clean up newlines for policy list
                lines = [line.strip() for line in d_detail.split("\n") if line.strip()]
                policies.extend(lines)

    seat_types = []
    group_status = raw.get("seat_group_status", [])
    if isinstance(group_status, list):
        for group in group_status:
            typ = group.get("type", "")
            qty = group.get("quantity", 0)
            if typ == "NGM":
                seat_types.append(f"Ngồi mềm ({qty})")
            elif typ == "NAM":
                seat_types.append(f"Giường khoang 4 ({qty})")
            elif typ == "NAC":
                seat_types.append(f"Giường khoang 6 ({qty})")
            else:
                seat_types.append(f"{typ} ({qty})")

    return TrainTicket(
        id_index=id_index,
        session_id=raw.get("session", ""),
        train_number=train_num,
        operator=operator,
        from_code=raw.get("start_point", ""),
        to_code=raw.get("end_point", ""),
        from_name=raw.get("departure_place", ""),
        to_name=raw.get("arrival_place", ""),
        departure_date=raw.get("date", ""),
        departure_time=raw.get("time", ""),
        arrival_date=raw.get("arrival_date", ""),
        arrival_time=raw.get("arrival_time", ""),
        duration_minutes=raw.get("duration", 0),
        distance_km=raw.get("distance", 0),
        seat_available=raw.get("seat_available", 0),
        min_price=min_price,
        cars=cars,
        utilities=list(set(utilities)),
        policies=list(set(policies)),
        promotions=promotions,
        description=raw.get("noi_dung_khuyen_mai", ""),
        seat_types=seat_types,
        raw=raw,
    )


async def search_trains(
    client: "TravelClient",
    from_code: str,
    to_code: str,
    date: str,
    passengers: int = 1,
    page: int = 1,
    sort: str = "fare:asc",
) -> list[TrainTicket]:
    """
    Search for train tickets.
    
    Args:
        client: TravelClient instance.
        from_code: Origin station code (e.g., "HNO").
        to_code: Destination station code (e.g., "SGO").
        date: Travel date in "YYYY-MM-DD" format.
        passengers: Number of passengers (default: 1).
        page: Result page (default: 1, 20 results per page).
        sort: Sort order (default: "fare:asc").
    
    Returns:
        List of TrainTicket objects, sorted by requested order.
    """
    tid = _time_id()
    params = {
        "filter[from][0]": from_code,
        "filter[to][0]": to_code,
        "filter[date]": date,
        "filter[quantity]": passengers,
        "filter[page]": page,
        "filter[time_id]": tid,
        "page": page,
        "sort": sort,
        "time_id": tid,
    }

    logger.debug(f"Searching trains: {from_code} -> {to_code} on {date}")

    try:
        data = await client._get(TRAIN_SEARCH_URL, params=params)
    except httpx.HTTPStatusError as e:
        logger.error(f"Train search failed: {e}")
        return []

    if data.get("message") != "success":
        logger.warning(f"Train search returned non-success: {data.get('message')}")
        return []

    tickets = []
    for item in data.get("data", []):
        try:
            tickets.append(_parse_train(item))
        except Exception as e:
            logger.warning(f"Failed to parse train item: {e}")

    logger.info(f"Found {len(tickets)} trains from {from_code} to {to_code} on {date}")
    return tickets


async def get_train_calendar(
    client: "TravelClient",
    from_code: str,
    to_code: str,
    month: int,
    year: int,
    passengers: int = 1,
) -> dict:
    """
    Get train availability calendar for a given month.
    
    Returns:
        dict with date strings as keys and availability/price info as values.
    """
    tid = _time_id()
    params = {
        "filter[from][0]": from_code,
        "filter[to][0]": to_code,
        "filter[month_years][0]": f"{month}-{year}",
        "filter[quantity]": passengers,
        "page": 1,
        "time_id": tid,
    }

    logger.debug(f"Getting train calendar: {from_code} -> {to_code} for {month}/{year}")

    try:
        data = await client._get(TRAIN_COUNT_URL, params=params)
    except httpx.HTTPStatusError as e:
        logger.error(f"Train calendar failed: {e}")
        return {}

    return data
