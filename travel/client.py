"""
Core TravelClient - the main entry point for TravelSDK.

Usage:
    import asyncio
    from travel import TravelClient

    async def main():
        async with TravelClient() as client:
            trains = await client.search_trains("Hà Nội", "Sài Gòn", "2026-04-20")
            for t in trains:
                print(f"{t.train_number} | {t.departure_time} | {t.min_price:,}đ")

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Any

import httpx

from travel.auth import TokenManager
from travel.constants import (
    DEFAULT_HEADERS,
    PROVIDER_BASE_URL,
    AREA_SEARCH_URL,
    AREA_DETAIL_URL,
)
from travel.locations import (
    resolve_train_station,
    resolve_flight_airport,
    resolve_bus_region,
    resolve_train_station_async,
    resolve_flight_airport_async,
    resolve_bus_region_async,
    get_all_provinces,
    get_all_airports,
    get_all_train_stations,
)
from travel.models import (
    TrainTicket,
    BusTicket,
    FlightTicket,
    SearchResult,
)
from travel import train as train_mod
from travel import bus as bus_mod
from travel import flight as flight_mod

logger = logging.getLogger(__name__)


class TravelClient:
    """
    Async HTTP client for Travel's internal transportation APIs.
    
    Provides:
    - search_trains(from, to, date): Search train tickets
    - search_buses(from, to, date): Search bus tickets
    - search_flights(from, to, date): Search flight tickets
    - search_all(from, to, date): Search all 3 simultaneously
    - get_train_calendar(from, to, month, year)
    - get_flight_calendar(from, to, month, year)
    
    Location inputs accept flexible formats:
    - Station codes: "HNO", "SGO"
    - IATA codes: "HAN", "SGN"
    - City names: "Hà Nội", "hanoi", "Sài Gòn"
    - Aliases: "hn", "hcm", "tphcm"
    
    Example:
        async with TravelClient() as client:
            results = await client.search_all("Hà Nội", "Sài Gòn", "2026-04-20")
            print(results.summary())
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 2,
        verbose: bool = False,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._token_manager = TokenManager()
        self._http_client: Optional[httpx.AsyncClient] = None

        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    # Context manager

    async def __aenter__(self) -> "TravelClient":
        await self._init_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _init_client(self) -> None:
        """Initialize the HTTP client and acquire the initial token."""
        self._http_client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        )
        # Pre-warm the token
        await self._token_manager.ensure_token(self._http_client)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # Location resolution helpers
    
    def resolve_train_station(self, query: str) -> Optional[dict]:
        """Resolve a city name or station code to train station info."""
        return resolve_train_station(query)

    def resolve_flight_airport(self, query: str) -> Optional[dict]:
        """Resolve a city name or IATA code to airport info."""
        return resolve_flight_airport(query)

    def resolve_bus_region(self, query: str) -> Optional[dict]:
        """Resolve a city name to its bus region ID."""
        return resolve_bus_region(query)

    def get_provinces(self) -> list[dict]:
        """Return a list of all 63 provinces in Vietnam from the local database."""
        return get_all_provinces()

    def get_airports(self) -> list[dict]:
        """Return a list of all airports in Vietnam from the local database."""
        return get_all_airports()

    def get_train_stations(self) -> list[dict]:
        """Return a list of all train stations in Vietnam from the local database."""
        return get_all_train_stations()

    async def resolve_train_station_async(self, query: str) -> Optional[dict]:
        """Async version of resolve_train_station with hierarchical discovery."""
        return await resolve_train_station_async(query, self)

    async def resolve_flight_airport_async(self, query: str) -> Optional[dict]:
        """Async version of resolve_flight_airport with hierarchical discovery."""
        return await resolve_flight_airport_async(query, self)

    async def resolve_bus_region_async(self, query: str) -> Optional[dict]:
        """Async version of resolve_bus_region with dynamic search fallback."""
        return await resolve_bus_region_async(query, self)

    # Internal request helper

    async def _get(self, url: str, params: dict | None = None) -> dict:
        """
        Make an authenticated GET request to a Travel API endpoint.
        Automatically refreshes the token if needed.
        """
        if not self._http_client:
            raise RuntimeError(
                "Client not initialized. Use 'async with TravelClient() as client:'"
            )

        bearer = await self._token_manager.ensure_token(self._http_client)
        headers = {
            "authorization": bearer,
            "origin-request-id": f"FE_NEXTJS_{int(time.time() * 1000)}_SDK",
        }

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._http_client.get(
                    url,
                    params=params,
                    headers=headers,
                )

                if response.status_code == 401:
                    # Token expired, force refresh
                    logger.debug("Token expired (401), refreshing...")
                    self._token_manager.invalidate()
                    bearer = await self._token_manager.ensure_token(self._http_client)
                    headers["authorization"] = bearer
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                if attempt < self._max_retries:
                    wait = 2 ** attempt
                    logger.warning(f"Request timed out. Retrying in {wait}s... (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                else:
                    raise
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self._max_retries:
                    wait = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    raise

        return {}

    async def search_areas(self, query: str) -> list[dict]:
        """
        Search for areas (provinces, cities, districts) by name.
        
        Args:
            query: Search string (e.g., "Quang Ninh")
        
        Returns:
            List of matching area dicts.
        """
        params = {"q": query, "is_merged_province": 1}
        data = await self._get(AREA_SEARCH_URL, params=params)
        return data.get("data", [])

    async def get_area_details(self, area_id: str | int) -> dict:
        """
        Get full details for a specific area.
        
        Args:
            area_id: The ID of the area (e.g., 49)
        
        Returns:
            Detailed area data dict.
        """
        url = f"{AREA_DETAIL_URL}/{area_id}"
        data = await self._get(url)
        return data.get("data", {})

    # Train search methods

    async def search_trains(
        self,
        from_location: str,
        to_location: str,
        date: str,
        passengers: int = 1,
        sort: str = "fare:asc",
    ) -> list[TrainTicket]:
        """
        Search for train tickets.
        
        Args:
            from_location: Origin (IATA code "HNO", city "Hà Nội", etc.).
            to_location: Destination.
            date: "YYYY-MM-DD".
            passengers: Number of passengers.
            sort: "fare:asc" | "fare:desc" | "departure_time:asc".
        
        Returns:
            List of TrainTicket objects.
        """
        from_info = await resolve_train_station_async(from_location, self)
        to_info = await resolve_train_station_async(to_location, self)

        if not from_info or not to_info:
            logger.error(f"Could not resolve locations: '{from_location}' or '{to_location}'")
            return []

        return await train_mod.search_trains(
            client=self,
            from_code=from_info["code"],
            to_code=to_info["code"],
            date=date,
            passengers=passengers,
            sort=sort,
        )

    async def get_train_calendar(
        self,
        from_location: str,
        to_location: str,
        month: int,
        year: int,
        passengers: int = 1,
    ) -> dict:
        """Get train availability calendar for a given month."""
        from_info = await resolve_train_station_async(from_location, self)
        to_info = await resolve_train_station_async(to_location, self)

        if not from_info or not to_info:
            return {}

        return await train_mod.get_train_calendar(
            client=self,
            from_code=from_info["code"],
            to_code=to_info["code"],
            month=month,
            year=year,
            passengers=passengers,
        )

    # Bus search methods

    async def search_buses(
        self,
        from_location: str | int,
        to_location: str | int,
        date: str,
        passengers: int = 1,
        sort: str = "fare:asc",
        page: int = 1,
        page_size: int = 20,
    ) -> list["BusTicket"]:
        """
        Search for bus tickets.
        
        Args:
            from_location: Origin city (name, region ID int, or string ID).
            to_location: Destination city.
            date: "YYYY-MM-DD".
            passengers: Number of passengers.
        
        Returns:
            List of BusTicket objects.
        """
        # Handle if integer IDs are passed directly
        if isinstance(from_location, int):
            from_id = from_location
        else:
            from_info = await resolve_bus_region_async(from_location, self)
            if not from_info:
                logger.error(f"Could not resolve bus region: '{from_location}'")
                return []
            from_id = from_info["id"]

        if isinstance(to_location, int):
            to_id = to_location
        else:
            to_info = await resolve_bus_region_async(to_location, self)
            if not to_info:
                logger.error(f"Could not resolve bus region: '{to_location}'")
                return []
            to_id = to_info["id"]

        return await bus_mod.search_buses(
            client=self,
            from_id=from_id,
            to_id=to_id,
            date=date,
            passengers=passengers,
            sort=sort,
            page=page,
            page_size=page_size,
        )

    # Flight search methods

    async def search_flights(
        self,
        from_location: str,
        to_location: str,
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
            from_location: Origin airport IATA code or city name.
            to_location: Destination airport IATA code or city name.
            date: "YYYY-MM-DD".
            passengers: Number of adult passengers.
            fare_class: "economy" or "business".
            sort: Sort order.
        
        Returns:
            List of FlightTicket objects.
        """
        from_info = await resolve_flight_airport_async(from_location, self)
        to_info = await resolve_flight_airport_async(to_location, self)

        if not from_info or not to_info:
            logger.error(f"Could not resolve airports: '{from_location}' or '{to_location}'")
            return []

        return await flight_mod.search_flights(
            client=self,
            from_iata=from_info["iata"],
            to_iata=to_info["iata"],
            date=date,
            passengers=passengers,
            fare_class=fare_class,
            page=page,
            page_size=page_size,
            sort=sort,
        )

    async def get_flight_calendar(
        self,
        from_location: str,
        to_location: str,
        month: int,
        year: int,
        passengers: int = 1,
    ) -> dict:
        """Get flight price calendar for a given month."""
        from_info = await resolve_flight_airport_async(from_location, self)
        to_info = await resolve_flight_airport_async(to_location, self)

        if not from_info or not to_info:
            return {}

        return await flight_mod.get_flight_calendar(
            client=self,
            from_iata=from_info["iata"],
            to_iata=to_info["iata"],
            month=month,
            year=year,
            passengers=passengers,
        )

    # Combined Search methods

    async def search_all(
        self,
        from_location: str,
        to_location: str,
        date: str,
        passengers: int = 1,
        include_trains: bool = True,
        include_buses: bool = True,
        include_flights: bool = True,
        page_size: int = 100,
    ) -> SearchResult:
        """
        Search for all transportation types simultaneously (parallel).
        
        Args:
            from_location: Origin location (flexible format).
            to_location: Destination location (flexible format).
            date: "YYYY-MM-DD".
            passengers: Number of passengers.
            include_trains: Whether to search trains (default: True).
            include_buses: Whether to search buses (default: True).
            include_flights: Whether to search flights (default: True).
        
        Returns:
            SearchResult containing all found tickets, sortable by price.
        
        Example:
            results = await client.search_all("Hà Nội", "Sài Gòn", "2026-04-20")
            print(results.summary())
            for ticket in results.all_tickets[:5]:  # Top 5 cheapest
                print(ticket)
        """
        tasks = []
        task_types = []

        if include_trains:
            tasks.append(self.search_trains(from_location, to_location, date, passengers))
            task_types.append("trains")

        if include_buses:
            tasks.append(self.search_buses(from_location, to_location, date, passengers, page_size=page_size))
            task_types.append("buses")

        if include_flights:
            tasks.append(self.search_flights(from_location, to_location, date, passengers, page_size=page_size))
            task_types.append("flights")

        # Run all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        trains: list[TrainTicket] = []
        buses: list[BusTicket] = []
        flights: list[FlightTicket] = []

        for ticket_type, result in zip(task_types, results):
            if isinstance(result, Exception):
                logger.warning(f"Search for {ticket_type} failed: {result}")
                continue
            if ticket_type == "trains":
                trains = result
            elif ticket_type == "buses":
                buses = result
            elif ticket_type == "flights":
                flights = result

        return SearchResult(
            query_from=from_location,
            query_to=to_location,
            query_date=date,
            query_passengers=passengers,
            trains=trains,
            buses=buses,
            flights=flights,
            searched_at=datetime.now().isoformat(),
        )
