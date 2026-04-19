
# TravelSDK for Python

[![PyPI version](https://img.shields.io/pypi/v/travel-sdk.svg)](https://pypi.org/project/travel-sdk/0.1.4/) [![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**TravelSDK** is a unified Python SDK for searching and comparing train, bus, and domestic flight tickets in Vietnam in real time. It returns Pydantic-validated data and is async-first, designed specifically for integration into **AI Agents** and **RAG pipelines**.

> **Disclaimer**: This is an unofficial SDK, not affiliated with Vexere, VNR, or any airline. For research and educational use only.

---

## Table of Contents

1. [Key Features](#1-key-features)
2. [Architecture](#2-architecture)
3. [Installation](#3-installation)
4. [Quickstart — Up and Running in 5 Minutes](#4-quickstart--up-and-running-in-5-minutes)
5. [Command Line Interface (CLI)](#5-command-line-interface-cli)
6. [Python API Reference](#6-python-api-reference)
   * [TravelClient](#travelclient)
   * [search_trains](#search_trains)
   * [search_buses](#search_buses)
   * [search_flights](#search_flights)
   * [search_all](#search_all)
   * [Calendar APIs](#calendar-apis)
   * [Location Resolution](#location-resolution)
7. [Data Schema](#7-data-schema)
   * [TrainTicket](#trainticket)
   * [BusTicket](#busticket)
   * [FlightTicket](#flightticket)
   * [SearchResult](#searchresult)
8. [Location Format](#8-location-format)
9. [Error Handling](#9-error-handling)
10. [AI Agent / RAG Integration](#10-ai-agent--rag-integration)
11. [Development & Testing](#11-development--testing)
12. [Changelog](#12-changelog)

---

## 1. Key Features

| Feature                   | Description                                                                                    |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| **Unified Search**        | Find trains + buses + flights in a single call, running in parallel                           |
| **Smart Fuzzy Matching**  | Type `"hnoi"`, `"hcm"`, `"sgn"` — the SDK resolves to the correct location automatically     |
| **Hierarchical Location** | Enter `"District 1"` or `"Cau Giay"` — the SDK resolves to the nearest transport hub          |
| **Offline Location DB**   | 63 provinces, 160+ train stations, all domestic airports — no network needed for lookup       |
| **Pydantic Models**       | All responses are validated, with full IDE autocomplete support                               |
| **Async-first**           | Built on `httpx` + `asyncio`, suitable for server-side applications                           |
| **Auto Token Refresh**    | Automatically handles token expiry with iterative retry (no recursion)                        |
| **AI-Ready**              | `summary()` method exports a dict optimized for LLM consumption                               |

---

## 2. Architecture

```
TravelClient
├── TokenManager          # Bearer token lifecycle (iterative auto-refresh)
├── search_trains()       # → train.py → TrainTicket[]
├── search_buses()        # → bus.py   → BusTicket[]
├── search_flights()      # → flight.py→ FlightTicket[]
├── search_all()          # asyncio.gather() → SearchResult
│
├── Location Resolution (2 layers)
│   ├── Layer 1 - Local DB  (all_locations.json, constants/)
│   │   └── Fuzzy Match     (difflib, cutoff=0.7)
│   └── Layer 2 - Remote API (search_areas → get_area_details)
│       └── Hub Resolution  (District → Province → hub)
│
└── CLI (travel-sdk)      # search + list subcommands
```

### Location Resolution Engine

The SDK uses a 2-layer strategy to resolve location names:

**Layer 1 — Local Cache (sync, zero-latency):**

* Exact match against station codes (`HNO`, `SGO`) or IATA codes (`HAN`, `SGN`)
* Fuzzy match via `difflib.get_close_matches` against names and aliases (cutoff 0.7)
* Lookup from `all_locations.json` (bundled, offline)
* Lookup from `constants/` (common names and aliases)

**Layer 2 — Remote API (async, fallback):**

* Calls `search_areas(query)` to get a list of matching areas
* Prioritizes Province type over District
* **Hub Resolution**: If a district has no hub (station/airport), automatically fetches the parent province to find the actual hub

---

## 3. Installation

**Requirements:** Python 3.9+

```bash
# Install from PyPI (stable)
pip install travel-sdk

# Install from GitHub (latest)
pip install git+https://github.com/Qhuy204/TravelSDK.git

# Install for development
git clone https://github.com/Qhuy204/TravelSDK.git
cd TravelSDK
pip install -e ".[dev]"
```

**Dependencies:**

* `httpx >= 0.27` — async HTTP client
* `pydantic >= 2.0` — data validation & serialization

---

## 4. Quickstart — Up and Running in 5 Minutes

### Search All Transport Modes

```python
import asyncio
from travel import TravelClient

async def main():
    async with TravelClient() as client:
        results = await client.search_all(
            from_location="Hanoi",
            to_location="Da Nang",
            date="2026-05-20",
            passengers=1,
        )

        print(f"Trains:  {len(results.trains)} results")
        print(f"Buses:   {len(results.buses)} results")
        print(f"Flights: {len(results.flights)} results")

        # Get the cheapest ticket across all modes
        cheapest = results.cheapest()
        if cheapest:
            print(f"\nCheapest: {cheapest}")

        # View top 5 cheapest tickets
        for ticket in results.all_tickets[:5]:
            print(ticket)

asyncio.run(main())
```

### Search Trains

```python
async with TravelClient() as client:
    trains = await client.search_trains(
        from_location="Hanoi",
        to_location="Saigon",
        date="2026-05-20",
    )

    for t in trains:
        print(f"{t.train_number} | {t.departure_time}→{t.arrival_time} | {t.min_price:,} VND | {t.seat_available} seats")
```

### Search Flights

```python
async with TravelClient() as client:
    flights = await client.search_flights(
        from_location="HAN",        # IATA code
        to_location="SGN",
        date="2026-05-20",
        passengers=2,
        fare_class="economy",       # or "business"
    )

    for f in flights:
        print(f"{f.flight_number} | {f.airline_name} | {f.departure_time} | {f.final_price:,} VND | {f.baggage_info}")
```

### Search Buses

```python
async with TravelClient() as client:
    buses = await client.search_buses(
        from_location="Hanoi",
        to_location="Hai Phong",
        date="2026-05-20",
    )

    for b in buses:
        print(f"{b.operator.name} | {b.bus_type} | {b.departure_time} | {b.final_price:,} VND | ⭐{b.rating}")
```

---

## 5. Command Line Interface (CLI)

After installation, the SDK exposes the `travel-sdk` command.

### Search

```bash
# Search all transport modes (default)
travel-sdk search --from "Hanoi" --to "Da Nang" --date "2026-05-20"

# Search by specific mode
travel-sdk search --from "Hanoi" --to "Saigon"   --date "2026-05-20" --mode train
travel-sdk search --from "Hai Phong" --to "Dalat" --date "2026-05-20" --mode flight
travel-sdk search --from "Hanoi" --to "Hai Phong" --date "2026-05-20" --mode bus

# Enable debug logging
travel-sdk search --from "Hanoi" --to "Da Nang" --date "2026-05-20" --verbose

# Fuzzy input works too
travel-sdk search --from "hnoi" --to "sgn" --date "2026-05-20"
```

**Flags:**

| Flag          | Value                              | Description                             |
| ------------- | ---------------------------------- | --------------------------------------- |
| `--from`    | string                             | Departure location (required)           |
| `--to`      | string                             | Destination (required)                  |
| `--date`    | `YYYY-MM-DD`                     | Travel date (default: today)            |
| `--mode`    | `all`, `train`, `bus`, `flight`  | Transport mode (default: `all`)         |
| `--verbose` | flag                               | Enable DEBUG logging                    |
| `--version` | flag                               | Display SDK version (from package metadata) |

### List Locations

```bash
# List all 63 provinces
travel-sdk list provinces

# List airports
travel-sdk list airports

# List train stations
travel-sdk list stations
```

---

## 6. Python API Reference

### TravelClient

The main entry point of the SDK. Manages tokens, connection pools, and retry logic.

```python
client = TravelClient(
    timeout=30.0,       # float — HTTP timeout in seconds. Default: 30.0
    max_retries=2,      # int   — Number of retries on timeout/5xx. Default: 2
    verbose=False,      # bool  — Enable DEBUG logging. Default: False
)
```

**Always use as an async context manager:**

```python
async with TravelClient() as client:
    # Client initializes tokens and HTTP pool automatically
    ...
# Client closes connections on exit
```

> Using `TravelClient()` without a context manager will raise `RuntimeError` when calling search methods. If you need standalone use, call `await client._init_client()` first.

---

### search_trains

```python
trains: list[TrainTicket] = await client.search_trains(
    from_location: str,           # Departure location
    to_location: str,             # Destination
    date: str,                    # "YYYY-MM-DD"
    passengers: int = 1,          # Number of passengers
    sort: str = "fare:asc",       # Sort order
)
```

**`sort` options:** `"fare:asc"` | `"fare:desc"` | `"departure_time:asc"`

**Returns:** `list[TrainTicket]` — list of train trips sorted by `sort`. Returns `[]` if no results or location cannot be resolved.

```python
trains = await client.search_trains("Hanoi", "Da Nang", "2026-05-20")
for t in trains:
    print(f"{t.train_number}: {t.departure_time}→{t.arrival_time} ({t.duration_str})")
    print(f"  From: {t.min_price:,} VND | Available: {t.seat_available} seats")
    for car in t.cars:
        print(f"  [{car.car_number}] {car.car_type}: {car.min_price:,} VND ({car.total_available} seats)")
```

---

### search_buses

```python
buses: list[BusTicket] = await client.search_buses(
    from_location: str | int,     # Province name or region ID (int)
    to_location: str | int,       # Province name or region ID (int)
    date: str,                    # "YYYY-MM-DD"
    passengers: int = 1,
    sort: str = "fare:asc",
    page: int = 1,                # Pagination
    page_size: int = 20,          # Results per page (max 100)
)
```

> **Tip:** You can pass a region ID directly (int) to skip the resolve step. See `travel-sdk list provinces` for ID list.

```python
buses = await client.search_buses("Hanoi", "Hai Phong", "2026-05-20")
for b in buses:
    print(f"{b.operator.name} ({b.bus_type}) | {b.departure_time} | {b.final_price:,} VND | ⭐{b.rating}")
    if b.pickup_points:
        print(f"  Pickup: {b.pickup_points[0].address}")
```

---

### search_flights

```python
flights: list[FlightTicket] = await client.search_flights(
    from_location: str,           # IATA code or province name
    to_location: str,             # IATA code or province name
    date: str,                    # "YYYY-MM-DD"
    passengers: int = 1,
    fare_class: str = "economy",  # "economy" | "business"
    page: int = 1,
    page_size: int = 20,
    sort: str = "fare:asc",
)
```

```python
flights = await client.search_flights("Hanoi", "Saigon", "2026-05-20", fare_class="business")
for f in flights:
    print(f"{f.flight_number} ({f.airline_name})")
    print(f"  {f.departure_time}→{f.arrival_time} | {f.duration_minutes // 60}h{f.duration_minutes % 60}m")
    print(f"  {f.final_price:,} VND | {f.baggage_info}")
    if f.utilities:
        print(f"  Amenities: {', '.join(f.utilities)}")
```

---

### search_all

Searches all 3 transport modes in parallel (`asyncio.gather`), returning a `SearchResult`.

```python
result: SearchResult = await client.search_all(
    from_location: str,
    to_location: str,
    date: str,
    passengers: int = 1,
    include_trains: bool = True,   # Include train results
    include_buses: bool = True,    # Include bus results
    include_flights: bool = True,  # Include flight results
    page_size: int = 100,          # Results per mode
)
```

If one mode fails, the remaining ones still return (errors are logged at WARNING level).

```python
result = await client.search_all("Hanoi", "Saigon", "2026-05-20")

# Iterate each mode separately
for t in result.trains:   ...
for b in result.buses:    ...
for f in result.flights:  ...

# All tickets sorted by price ascending
for ticket in result.all_tickets:
    print(ticket)

# Overall cheapest ticket
cheapest = result.cheapest()

# Sort by different criteria
by_time = result.sort_tickets(result.trains, by="time")
by_airline = result.sort_tickets(result.flights, by="airline")

# Summary dict (ideal for LLM context)
summary = result.summary()
# {
#   "from": "Hanoi", "to": "Saigon", "date": "2026-05-20",
#   "train_count": 8, "bus_count": 42, "flight_count": 15,
#   "cheapest_train": 380000, "cheapest_bus": 180000, "cheapest_flight": 990000,
#   "top_train_info": "Train SE9 (07:00) - 380000 VND",
#   "top_bus_info": "Phuong Trang Bus (06:00) - 180000 VND",
#   "top_flight_info": "VietJet (06:30) - 990000 VND"
# }
```

---

### Calendar APIs

Get monthly price calendars for UI display or agent trip planning.

```python
# Train price calendar for May 2026
train_calendar: dict = await client.get_train_calendar(
    from_location="Hanoi",
    to_location="Saigon",
    month=5,
    year=2026,
    passengers=1,
)

# Flight price calendar for May 2026
flight_calendar: dict = await client.get_flight_calendar(
    from_location="HAN",
    to_location="SGN",
    month=5,
    year=2026,
    passengers=1,
)
```

---

### Location Resolution

Use when you need to resolve a location manually without performing a search.

```python
# --- Sync (uses local DB, zero-latency) ---
station = client.resolve_train_station("Hanoi")
# {"code": "HNO", "name": "Ha Noi Station", "location_id": 1, ...}

airport = client.resolve_flight_airport("SGN")
# {"iata": "SGN", "name": "Tan Son Nhat", "city": "Ho Chi Minh City", ...}

bus_region = client.resolve_bus_region("Da Nang")
# {"id": 15, "name": "Da Nang", "slug": "da-nang"}

# --- Async (with API fallback + hub resolution) ---
station = await client.resolve_train_station_async("Cau Giay")
# Resolves: Cau Giay (district) → Hanoi (province) → Ha Noi Station

airport = await client.resolve_flight_airport_async("District 1")
# Resolves: District 1 → Ho Chi Minh City → Tan Son Nhat Airport

# --- Offline DB helpers ---
provinces = client.get_provinces()      # list[dict] — 63 provinces
airports  = client.get_airports()       # list[dict] — all airports
stations  = client.get_train_stations() # list[dict] — all train stations
```

---

## 7. Data Schema

### TrainTicket

```python
class TrainTicket(BaseModel):
    type: TicketType               # Always TicketType.TRAIN
    id_index: str                  # Internal API ID
    train_number: str              # Train code, e.g. "SE9", "TN1"
    operator: Provider             # {"code": "VNR", "name": "Vietnam Railways"}

    from_code: str                 # Departure station code, e.g. "HNO"
    to_code: str                   # Arrival station code, e.g. "SGO"
    from_name: str                 # Departure station name
    to_name: str                   # Arrival station name

    departure_date: str            # "YYYY-MM-DD"
    departure_time: str            # "HH:MM"
    arrival_date: str              # "YYYY-MM-DD"
    arrival_time: str              # "HH:MM"
    duration_minutes: int          # Travel duration in minutes
    duration_str: str              # Property: "32h05m"
    distance_km: int               # Distance in km

    min_price: int                 # Lowest price (VND)
    seat_available: int            # Total available seats
    cars: list[CarInfo]            # Per-car details (see CarInfo below)

    seat_types: list[str]          # Available seat types, e.g. ["Soft Seat", "6-Berth Sleeper"]
    utilities: list[str]           # Amenities, e.g. ["Air Conditioning", "WiFi"]
    policies: list[str]            # Policies, e.g. ["Refund 24h before departure"]
    promotions: list[str]          # Promotions
    baggage_info: str              # Baggage information
    description: str               # Trip description
    images: list[str]              # Image URLs
    highlights: list[str]          # Highlights
```

**CarInfo** (part of `TrainTicket.cars`):

```python
class CarInfo(BaseModel):
    car_id: int
    car_number: str                # "1", "2A"
    car_type: str                  # "Air-conditioned Soft Seat", "6-Berth Sleeper"
    group_code: str                # "NGM", "NAC", "NAM"
    total_available: int           # Available seats in this car
    min_price: int                 # Lowest price in this car (VND)
    seat_options: list[SeatOption] # Details per seat/berth type
```

**SeatOption** (part of `CarInfo.seat_options`):

```python
class SeatOption(BaseModel):
    code: str                      # Internal code
    label: str                     # Display name, e.g. "4-Berth AC Sleeper"
    seat_class: SeatClass          # Enum: SOFT_SEAT, HARD_SEAT, SLEEPER_6, SLEEPER_4, VIP, ...
    price: int                     # Base price (VND)
    markup_price: Optional[int]    # Price after markup
    available: int                 # Remaining seats
```

---

### BusTicket

```python
class BusTicket(BaseModel):
    type: TicketType               # Always TicketType.BUS
    operator: Provider             # {"code": "...", "name": "Phuong Trang"}

    from_id: int                   # Bus region ID for departure
    to_id: int                     # Bus region ID for destination
    from_name: str
    to_name: str

    departure_date: str            # "YYYY-MM-DD"
    departure_time: str            # "HH:MM"
    arrival_time: str              # "HH:MM"
    duration_minutes: int

    bus_type: str                  # "Limousine", "40-seat Sleeper", "Sleeper VIP"
    seat_available: int

    price: int                     # Base price (VND)
    final_price: int               # Price after discount (VND)

    pickup_points: list[PointInfo] # Pickup locations
    dropoff_points: list[PointInfo]# Drop-off locations

    rating: float                  # Average rating (0.0–5.0)
    reviews: int                   # Number of reviews

    utilities: list[str]           # Amenities, e.g. ["WiFi", "AC", "USB Charger"]
    policies: list[str]
    promotions: list[str]
    baggage_info: str
    description: str
```

**PointInfo** (part of `BusTicket.pickup_points` / `dropoff_points`):

```python
class PointInfo(BaseModel):
    name: str                      # Stop name
    address: str                   # Full address
    time_offset_minutes: int       # Offset from departure time
    lat: float                     # Latitude
    lon: float                     # Longitude
```

---

### FlightTicket

```python
class FlightTicket(BaseModel):
    type: TicketType               # Always TicketType.FLIGHT
    id_index: str                  # Internal ID

    airline_code: str              # "VJ", "VN", "QH", "BL"
    airline_name: str              # "VietJet Air", "Vietnam Airlines"
    flight_number: str             # "VJ123", "VN204"
    cabin: str                     # "Economy", "Business"
    airplane_name: str             # "Airbus A321", "Boeing 787"
    is_non_stop: bool              # True if direct flight

    from_iata: str                 # "HAN", "DAD", "SGN"
    to_iata: str
    from_name: str
    to_name: str

    departure_date: str            # "YYYY-MM-DD"
    departure_time: str            # "HH:MM"
    arrival_time: str              # "HH:MM"
    duration_minutes: int

    price: int                     # Pre-tax price (VND)
    final_price: int               # All-inclusive price (VND)

    baggage_info: str              # "7kg carry-on + 20kg checked"
    utilities: list[str]           # Included amenities
    policies: list[str]            # Change/refund policies
    promotions: list[str]
    description: str
```

---

### SearchResult

Object returned by `search_all()`.

```python
class SearchResult(BaseModel):
    query_from: str
    query_to: str
    query_date: str
    query_passengers: int

    trains: list[TrainTicket]
    buses: list[BusTicket]
    flights: list[FlightTicket]

    searched_at: Optional[str]     # ISO timestamp

    # Properties & Methods:
    all_tickets                    # property: all tickets sorted by price ascending
    cheapest()                     # → the overall cheapest ticket
    summary()                      # → summary dict (see below)
    sort_tickets(tickets, by, reverse)  # sort by "price", "time", "airline"/"operator"
```

**`summary()` output:**

```python
{
    "from": "Hanoi",
    "to": "Saigon",
    "date": "2026-05-20",
    "train_count": 8,
    "bus_count": 42,
    "flight_count": 15,
    "cheapest_train": 380000,      # VND, or None if not available
    "cheapest_bus": 180000,
    "cheapest_flight": 990000,
    "top_train_info": "Train SE9 (07:00) - 380000 VND",
    "top_bus_info": "Phuong Trang Bus (06:00) - 180000 VND",
    "top_flight_info": "VietJet (06:30) - 990000 VND"
}
```

---

## 8. Location Format

The SDK accepts multiple location input formats:

| Input               | Type            | Example                                                  |
| ------------------- | --------------- | -------------------------------------------------------- |
| Province/city name  | Fuzzy match     | `"Ha Noi"`, `"hanoi"`, `"Saigon"`, `"tp hcm"`          |
| Common alias        | Hard mapping    | `"hn"`, `"hcm"`, `"tphcm"`, `"sgn"`                    |
| IATA code           | Exact match     | `"HAN"`, `"SGN"`, `"DAD"`, `"HUI"`                     |
| Train station code  | Exact match     | `"HNO"`, `"SGO"`, `"DAN"`                              |
| District/ward name  | Hub resolution  | `"District 1"`, `"Cau Giay"`, `"Hoan Kiem"`            |
| Bus region ID       | Direct (int)    | `1`, `34`, `2`                                          |

**Fuzzy matching** is powered by `difflib.get_close_matches` with a threshold of 0.7, so minor typos like `"hnoi"` or `"danang"` are resolved correctly.

**Main airport IATA codes:**

| Airport            | IATA    | Province                  |
| ------------------- | ------- | ------------------------- |
| Noi Bai            | `HAN` | Hanoi                     |
| Tan Son Nhat       | `SGN` | Ho Chi Minh City          |
| Da Nang            | `DAD` | Da Nang                   |
| Cam Ranh           | `CXR` | Khanh Hoa (Nha Trang)     |
| Phu Quoc           | `PQC` | Kien Giang                |
| Cat Bi             | `HPH` | Hai Phong                 |
| Phu Bai            | `HUI` | Thua Thien Hue            |
| Lien Khuong        | `DLI` | Lam Dong (Da Lat)         |
| Can Tho            | `VCA` | Can Tho                   |

**Main train station codes:**

| Station    | Code    |
| ---------- | ------- |
| Ha Noi     | `HNO` |
| Sai Gon    | `SGO` |
| Da Nang    | `DAN` |
| Hue        | `HUE` |
| Nha Trang  | `NTR` |

See full lists: `travel-sdk list stations` or `travel-sdk list airports`

---

## 9. Error Handling

### Location Not Found

The SDK returns `[]` (empty list) instead of raising an exception when a location cannot be resolved. Check logs to debug:

```python
import logging
logging.basicConfig(level=logging.INFO)

async with TravelClient() as client:
    trains = await client.search_trains("XYZ nowhere", "Da Nang", "2026-05-20")
    if not trains:
        print("No trains found — check the location name")
```

### Network Errors & Retry

`TravelClient` automatically retries on:

* `httpx.TimeoutException` → retry with exponential backoff (1s, 2s)
* HTTP 5xx → retry with exponential backoff
* HTTP 401 → refresh token then retry

After retries are exhausted, the exception is raised for the application to handle:

```python
import httpx

try:
    async with TravelClient(timeout=10.0, max_retries=3) as client:
        trains = await client.search_trains("Hanoi", "Da Nang", "2026-05-20")
except httpx.TimeoutException:
    print("Request timed out after 10 seconds")
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Partial Failure in search_all

If one mode fails in `search_all`, the remaining modes still return results:

```python
result = await client.search_all("Hanoi", "Saigon", "2026-05-20")
# If search_flights fails → result.flights = [], trains and buses still have data
# Errors are logged at WARNING level
```

---

## 10. AI Agent / RAG Integration

The SDK is optimized for integration into LLM agents. Recommended patterns:

### Use `summary()` as LLM Context

```python
async def search_travel_for_agent(origin: str, destination: str, date: str) -> str:
    """Tool function for an LLM agent."""
    async with TravelClient() as client:
        result = await client.search_all(origin, destination, date)
        summary = result.summary()

    return f"""
Travel search results: {summary['from']} → {summary['to']} on {summary['date']}

Flights: {summary['flight_count']} options, cheapest at {summary.get('cheapest_flight', 'N/A')} VND
{summary.get('top_flight_info', 'None available')}

Trains: {summary['train_count']} options, cheapest at {summary.get('cheapest_train', 'N/A')} VND
{summary.get('top_train_info', 'None available')}

Buses: {summary['bus_count']} options, cheapest at {summary.get('cheapest_bus', 'N/A')} VND
{summary.get('top_bus_info', 'None available')}
""".strip()
```

### Tool Definition for OpenAI / Claude Function Calling

```python
travel_search_tool = {
    "name": "search_travel",
    "description": "Search for real-time train, bus, and domestic flight tickets in Vietnam.",
    "parameters": {
        "type": "object",
        "properties": {
            "from_location": {
                "type": "string",
                "description": "Departure location (province name, IATA code, or station code)"
            },
            "to_location": {
                "type": "string",
                "description": "Destination"
            },
            "date": {
                "type": "string",
                "description": "Travel date in YYYY-MM-DD format"
            },
            "mode": {
                "type": "string",
                "enum": ["all", "train", "bus", "flight"],
                "description": "Transport mode to search"
            }
        },
        "required": ["from_location", "to_location", "date"]
    }
}
```

### Handling Tool Calls in an Agent

```python
async def handle_tool_call(tool_name: str, args: dict) -> str:
    if tool_name == "search_travel":
        async with TravelClient() as client:
            mode = args.get("mode", "all")
            date = args["date"]
            origin = args["from_location"]
            dest = args["to_location"]

            if mode == "train":
                tickets = await client.search_trains(origin, dest, date)
                return format_trains(tickets)
            elif mode == "flight":
                tickets = await client.search_flights(origin, dest, date)
                return format_flights(tickets)
            elif mode == "bus":
                tickets = await client.search_buses(origin, dest, date)
                return format_buses(tickets)
            else:
                result = await client.search_all(origin, dest, date)
                return str(result.summary())
```

---

## 11. Development & Testing

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
# Includes: pytest, pytest-asyncio, python-dotenv
```

### Run Tests

```bash
# All tests
pytest tests/

# Location resolution tests (offline, no API needed)
pytest tests/test_locations.py

# Model tests (offline)
pytest tests/test_models.py

# Live API tests (requires internet)
pytest tests/test_live_api.py -v

# With verbose output and Windows UTF-8 support
$env:PYTHONUTF8=1; pytest tests/ -v

# With detailed logging
pytest tests/ -v --log-cli-level=DEBUG
```

### Project Structure

```
TravelSDK/
├── travel/                     # Main package
│   ├── __init__.py             # Public API exports
│   ├── client.py               # TravelClient entry point
│   ├── auth.py                 # TokenManager (iterative refresh)
│   ├── flight.py               # Flight search logic
│   ├── train.py                # Train search logic
│   ├── bus.py                  # Bus search logic
│   ├── locations.py            # Location resolution engine (fuzzy matching)
│   ├── cli.py                  # CLI entry point
│   ├── py.typed                # PEP 561 marker
│   ├── constants/              # URLs, province codes, station codes
│   │   ├── locations.py
│   │   ├── transport.py
│   │   └── urls.py
│   ├── models/                 # Pydantic schemas
│   │   ├── base.py             # TicketType, Provider, SeatOption, PointInfo
│   │   ├── train.py            # TrainTicket, CarInfo
│   │   ├── bus.py              # BusTicket
│   │   ├── flight.py           # FlightTicket
│   │   └── search.py           # SearchResult
│   └── data/
│       └── all_locations.json  # Offline location database
├── tests/                      # Unit & integration tests
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_locations.py
│   ├── test_models.py
│   ├── test_live_api.py
│   └── test_real_searches.py
├── examples/                   # Usage examples
│   └── search_demo.py
├── CHANGELOG.md
├── pyproject.toml
└── README.md
```

---

## 12. Changelog

### v0.1.4 (2026-04-19)

* **English Documentation**: Rewrote full README in English for broader audience.
* **Version Alignment**: Fixed `pyproject.toml` version mismatch that caused PyPI upload conflicts.

### v0.1.3 (2026-04-19)

* **Smart Fuzzy Matching**: Integrated `difflib.get_close_matches` for all 3 modes — Train, Flight, Bus. Input like `hnoi`, `sgn`, `hcm` is resolved automatically.
* **CLI Bug Fix**: Fixed `AttributeError` when displaying bus results (`b.operator_name` → `b.operator.name`).
* **Dynamic Versioning**: `--version` flag reads from package metadata instead of hardcoded string.
* **Accurate `summary()`**: Uses `min()` instead of `[0]` to guarantee the lowest price is always correct.
* **Auth Stability**: Refactored `TokenManager._acquire()` to use iterative retry loop, eliminating recursion-caused `RuntimeError: Event loop is closed`.
* **PEP 561**: Added `travel/py.typed` marker for full IDE type hint support.
* **Test Suite**: Converted all test scripts to standard `pytest-asyncio`. Added `tests/conftest.py`, achieving 35/35 tests passed.
* **Structure**: Moved test files into `tests/`, added `scratch/` to `.gitignore`.

### v0.1.2 (2026-04-19)

* Added `include_trains/buses/flights` flags to `search_all`
* Improved hierarchical hub resolution for district-level queries
* CLI: added `--mode` flag and `--list`/`--search` aliases
* Fixed PyPI version conflict by bumping version

### v0.1.1 (2026-04-19)

* Fixed token invalidation on 401 responses
* Added exponential backoff for retries
* Registered `travel-sdk` CLI entry point

### v0.1.0 (2026-04-18)

* Initial release
* Unified search API for trains, buses, and flights
* Offline location database (63 provinces, 160+ stations, all domestic airports)
* Hierarchical location resolution (District → Province Hub)

---

## License

MIT License — Copyright (c) 2026 [Qhuy204](https://github.com/Qhuy204)

> This SDK is unofficial and not endorsed by Vexere, VNR, or any airline. For research and educational use only.
