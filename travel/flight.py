"""
Flight search module for TravelSDK.
Wraps /v2/route/flight endpoint.
"""

from __future__ import annotations

import json as _json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

from travel.constants import (
    FLIGHT_SEARCH_URL,
    FLIGHT_COUNT_URL,
    ECONOMY_FARE_CLASSES,
    ECONOMY_CABIN_CLASSES,
    PROVIDER_BASE_URL,
)
from travel.models import FlightTicket, Provider

if TYPE_CHECKING:
    from travel.client import TravelClient

logger = logging.getLogger(__name__)

# Known airline names (fallback if company field is empty)
AIRLINE_NAMES = {
    "VN": "Vietnam Airlines",
    "VJ": "VietJet Air",
    "9G": "Pacific Airlines",
    "QH": "Bamboo Airways",
    "VU": "Vietravel Airlines",
    "BL": "Pacific Airlines",
}


def _time_id() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _build_fare_class_params(fare_classes: list[str]) -> dict:
    return {f"filter[fare_class][{i}]": fc for i, fc in enumerate(fare_classes)}


def _build_cabin_params(cabin_classes: list[str]) -> dict:
    return {f"filter[cabin][{i}]": cc for i, cc in enumerate(cabin_classes)}


def _parse_flight(raw: dict) -> FlightTicket:
    """
    Parse a raw Travel flight result dict into a FlightTicket model.

    Key fields discovered from live API debug:
      - flight_number: "VU791" (string)
      - time: "21:05"  (departure time)
      - arrival_time: "23:15"
      - arrival_date: "2026-04-25"
      - duration: 130  (minutes)
      - seat_available: 29
      - date: "2026-04-25"
      - airline: "VU"
      - cabin: derived from idIndex part[8]
      - company: {"name": "Vietravel Airlines", "code": "VU", ...}
      - departure_place: "Sân bay Nội Bài"
      - to_area: {"name": "Sân bay Tân Sơn Nhất", ...}
      - start_point: "HAN", end_point: "SGN"
      - idIndex: "VU|R|VU791|0|2026-04-25|21:05|102188|28284|ECONOMY|100"

    Note: Per-item prices are NOT embedded. They are loaded lazily via
    fare_data_id via a separate pricing call. Only root-level min/max_price_data
    is available from the list response.
    """
    id_index = raw.get("idIndex", "")
    parts = id_index.split("|") if id_index else []

    # Airline code
    airline_code = raw.get("airline", parts[0] if parts else "")

    # Flight number (prefer direct field over parsed idIndex)
    flight_number = raw.get("flight_number", "")
    if not flight_number and len(parts) > 2:
        flight_number = parts[2]

    # Departure/arrival times
    dep_date = raw.get("date", parts[4] if len(parts) > 4 else "")
    dep_time = raw.get("time", parts[5] if len(parts) > 5 else "")
    arrival_time = raw.get("arrival_time", "")
    arrival_date = raw.get("arrival_date", dep_date)

    # Cabin class from idIndex part[8]
    cabin = parts[8] if len(parts) > 8 else "Economy"

    # Duration is directly available
    duration_minutes = raw.get("duration", 0)

    # Price: Travel embeds per-item prices in the route -> schedules array
    price = 0
    final_price = 0
    route_obj = raw.get("route", {})
    if isinstance(route_obj, dict):
        schedules = route_obj.get("schedules", [])
        if schedules and isinstance(schedules, list):
            first_schedule = schedules[0]
            if isinstance(first_schedule, dict):
                final_price = int(
                    first_schedule.get("final_price_adult")
                    or first_schedule.get("total_price_adult")
                    or first_schedule.get("total_net_price")
                    or first_schedule.get("total_price")
                    or 0
                )
                price = int(
                    first_schedule.get("fare_adult")
                    or final_price
                )

    # Fallback to direct fields (sometimes injected or used in different formats)
    if not price:
        price = int(raw.get("price") or raw.get("fare") or 0)
    if not final_price:
        final_price = int(raw.get("finalPrice") or raw.get("total_price") or price)

    # IATA codes from start_point/end_point (or passed in from caller)
    from_iata = raw.get("from_iata") or raw.get("start_point", "")
    to_iata = raw.get("to_iata") or raw.get("end_point", "")

    # Human-readable location names
    from_name = raw.get("departure_place", "")
    to_area = raw.get("to_area", {})
    to_name = to_area.get("name", "") if isinstance(to_area, dict) else ""

    # Airline name: prefer company dict, fallback to constants
    airline_name = ""
    company_raw = raw.get("company", {})
    if isinstance(company_raw, dict):
        airline_name = company_raw.get("name", "")

    # Rich Details Extraciton
    from travel.constants.transport import AIRCRAFT_MAPPING
    
    utilities = []
    policies = []
    promotions = []
    baggage_str = ""
    description = ""
    airplane_name = ""
    is_non_stop = True

    # Coupons / promotions at root level
    for coup in raw.get("coupons", []):
        if isinstance(coup, dict) and coup.get("campaign_name"):
            promotions.append(coup.get("campaign_name"))

    segments = raw.get("segments", [])
    if segments and isinstance(segments, list) and isinstance(segments[0], dict):
        seg = segments[0]
        # Stops
        if seg.get("has_stop", 0) > 0:
            is_non_stop = False
            
        # Aircraft type
        plane_code = str(seg.get("plane", ""))
        f_num = seg.get("flight_number", flight_number)
        
        airplane_name = AIRCRAFT_MAPPING.get(plane_code)
        if not airplane_name:
            # Fallback guessing if not in mapping
            if plane_code.startswith("3"):
                airplane_name = f"Airbus A{plane_code}"
            elif plane_code.startswith("7"):
                airplane_name = f"Boeing {plane_code}"
            else:
                airplane_name = f"Máy bay {plane_code}" if plane_code else ""
        
        if airplane_name:
            airplane_name = f"{airplane_name} (Chuyến {f_num})"
        else:
            airplane_name = f"Chuyến {f_num}"

    # Fare rules processing for food, refund, baggage, score
    fare_rules = raw.get("fare_rules", [])
    if fare_rules and isinstance(fare_rules, list) and isinstance(fare_rules[0], dict):
        rule = fare_rules[0]
        
        # Food
        if str(rule.get("is_meal", "")).lower() == "yes":
            utilities.append("Bao gồm suất ăn")
        elif str(rule.get("is_meal", "")).lower() == "no":
            utilities.append("Không bao gồm suất ăn")
            
        # Baggage allowance
        baggages_allowance = []
        if segments and segments[0].get("hand_baggage"):
            baggages_allowance.append(f'{segments[0].get("hand_baggage")} hành lý xách tay')
            
        weight = rule.get("baggage_weight")
        qty = rule.get("baggage_quantity")
        if str(rule.get("is_baggage", "")).lower() == "yes" and weight:
            qty_str = f"{qty} kiện x " if qty and str(qty) != "0" else ""
            baggages_allowance.append(f"{qty_str}{weight}kg hành lý ký gửi")
            
        if baggages_allowance:
            baggage_str = " | ".join(baggages_allowance)

        # Refund & Update
        if str(rule.get("is_refund_1", "")).lower() == "yes" or str(rule.get("is_refund_2", "")).lower() == "yes":
            policies.append("Được phép hoàn vé")
        else:
            policies.append("Không được phép hoàn vé")
        
        if str(rule.get("is_update_ticket_1", "")).lower() == "yes" or str(rule.get("is_update_ticket_2", "")).lower() == "yes":
            policies.append("Được phép đổi vé")
        else:
            policies.append("Không được phép đổi vé")
            
        # Score
        score = rule.get("has_plus_point")
        if score and str(score).lower() != "no":
            policies.append(f"Hệ số cộng điểm: {score}")

    # Extra bought Baggage Info (Pricing)
    baggages = raw.get("baggages", [])
    if baggages and isinstance(baggages, list):
        bg_list = []
        for bg in baggages:
            bname = bg.get("name", "")
            bprice = bg.get("price", 0)
            if bname:
                bg_list.append(f"{bname} ({bprice:,}đ)")
        if bg_list:
            if baggage_str:
                baggage_str += " -- Mua thêm: "
            baggage_str += ", ".join(bg_list)

    if not airline_name:
        payload = raw.get("payload_book_flight")
        if isinstance(payload, str):
            try:
                pb = _json.loads(payload)
                airline_name = pb.get("airlineName", "")
            except Exception:
                pass
        elif isinstance(payload, dict):
            airline_name = payload.get("airlineName", "")

    airline_name = airline_name or AIRLINE_NAMES.get(airline_code, airline_code)

    # Build return model

    return FlightTicket(
        id_index=id_index,
        airline_code=airline_code,
        flight_number=flight_number,
        cabin=cabin,
        from_iata=from_iata,
        to_iata=to_iata,
        from_name=from_name,
        to_name=to_name,
        departure_date=dep_date,
        departure_time=dep_time,
        arrival_time=arrival_time,
        duration_minutes=duration_minutes,
        price=price,
        final_price=final_price,
        airline_name=airline_name or airline_code,
        description=description,
        airplane_name=airplane_name,
        is_non_stop=is_non_stop,
        utilities=utilities,
        policies=policies,
        promotions=promotions,
        baggage_info=baggage_str,
        raw=raw,
    )


async def search_flights(
    client: "TravelClient",
    from_iata: str,
    to_iata: str,
    date: str,
    passengers: int = 1,
    fare_class: str = "economy",
    page: int = 1,
    page_size: int = 20,
    sort: str = "fare:asc",
) -> list[FlightTicket]:
    """
    Search for flight tickets.

    Args:
        client: TravelClient instance.
        from_iata: Departure airport IATA code (e.g., "HAN").
        to_iata: Destination airport IATA code (e.g., "SGN").
        date: Travel date in "YYYY-MM-DD" format.
        passengers: Number of adult passengers (default: 1).
        fare_class: "economy" or "business" (default: "economy").
        page: Result page (default: 1).
        page_size: Results per page (default: 20).
        sort: Sort order (default: "fare:asc").

    Returns:
        List of FlightTicket objects. Note: individual ticket prices are
        not available from the list API (loaded lazily by Travel). Use
        min_price range from the response root for budget estimates.
    """
    tid = _time_id()

    if fare_class == "business":
        fare_classes = ["J", "C", "D", "I", "Z"]
        cabin_classes = ["business"]
    else:
        fare_classes = ECONOMY_FARE_CLASSES
        cabin_classes = ECONOMY_CABIN_CLASSES

    params: dict = {
        "filter[date]": date,
        "filter[from][0]": from_iata,
        "filter[to][0]": to_iata,
        "filter[quantity]": passengers,
        "filter[time_id]": tid,
        "filter[child_infant_count]": 0,
        "filter[infant_count]": 0,
        "filter[is_group_ticket]": 0,
        "filter[show_gom_ve]": 1,
        "filter[page]": page,
        "filter[pagesize]": page_size,
        "page": page,
        "pagesize": page_size,
        "sort": sort,
        "is_group_ticket": 0,
        "show_gom_ve": 1,
        "time_id": tid,
    }
    params.update(_build_fare_class_params(fare_classes))
    params.update(_build_cabin_params(cabin_classes))

    logger.debug(f"Searching flights: {from_iata} -> {to_iata} on {date}")

    try:
        data = await client._get(FLIGHT_SEARCH_URL, params=params)
    except httpx.HTTPStatusError as e:
        logger.error(f"Flight search failed: {e}")
        return []

    if data.get("message") != "success":
        logger.warning(f"Flight search returned non-success: {data.get('message')}")
        return []

    # Enrich items with IATA codes (needed since API doesn't always return them)
    tickets = []
    for item in data.get("data", []):
        try:
            item.setdefault("from_iata", from_iata)
            item.setdefault("to_iata", to_iata)
            tickets.append(_parse_flight(item))
        except Exception as e:
            logger.warning(f"Failed to parse flight item: {e}")

    # Log price range from root (this is where prices actually live in list response)
    min_pd = data.get("min_price_data", {})
    max_pd = data.get("max_price_data", {})
    total = data.get("total", len(tickets))
    if min_pd and min_pd.get('price') is not None:
        min_p = min_pd.get('price', 0)
        max_p = max_pd.get('price', 0)
        logger.info(
            f"Found {len(tickets)}/{total} flights {from_iata}→{to_iata} on {date} | "
            f"Price: {min_p:,}–{max_p:,} VND"
        )
    else:
        logger.info(f"Found {len(tickets)}/{total} flights from {from_iata} to {to_iata} on {date}")

    return tickets


async def get_flight_calendar(
    client: "TravelClient",
    from_iata: str,
    to_iata: str,
    month: int,
    year: int,
    passengers: int = 1,
) -> dict:
    """
    Get flight availability/price calendar for a given month.

    Returns:
        Raw API response dict with date-based pricing.
    """
    import calendar

    _, last_day = calendar.monthrange(year, month)
    date_min = f"{year}-{month:02d}-01"
    date_max = f"{year}-{month:02d}-{last_day:02d}"

    tid = _time_id()
    params: dict = {
        "filter[from][0]": from_iata,
        "filter[to][0]": to_iata,
        "filter[date_range][min]": date_min,
        "filter[date_range][max]": date_max,
        "filter[month_years][0]": f"{month}-{year}",
        "filter[quantity]": passengers,
        "filter[child_infant_count]": 0,
        "filter[infant_count]": 0,
        "filter[is_count_tet_price]": 0,
        "filter[selected_date]": date_min,
        "filter[is_group_ticket]": 0,
        "filter[time_id]": tid,
        "is_group_ticket": 0,
        "time_id": tid,
    }
    params.update(_build_fare_class_params(ECONOMY_FARE_CLASSES))
    params.update(_build_cabin_params(ECONOMY_CABIN_CLASSES))

    logger.debug(f"Getting flight calendar: {from_iata} -> {to_iata} for {month}/{year}")

    try:
        data = await client._get(FLIGHT_COUNT_URL, params=params)
    except httpx.HTTPStatusError as e:
        logger.error(f"Flight calendar failed: {e}")
        return {}

    return data
