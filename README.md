# TravelSDK for Python

[![PyPI version](https://img.shields.io/pypi/v/travel-sdk.svg)](https://pypi.org/project/travel-sdk/) [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/Qhuy204/TravelSDK) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

TravelSDK is a high-performance Python library designed to provide a single, consistent interface for searching and managing transportation data across Vietnam. By aggregating data from Vietnam Railways (VNR), dozens of domestic airlines, and hundreds of bus operators, TravelSDK simplifies the complexity of integrating fragmented transportation services into your applications.

---

## 1. Project Overview

The primary goal of TravelSDK is to empower developers building travel booking systems, data analysis pipelines, and intelligent AI agents (RAG) with structured, reliable transportation data.

### Key Features

* **Unified Search Interface**: Query trains, buses, and flights using a single method call.
* **Hierarchical Location Discovery**: Automatically resolves vague location names (e.g., "District 1") to their nearest provincial transportation hubs.
* **Built-in Location Database**: Includes an offline-first database of over 60 provinces, 160+ train stations, and all domestic airports.
* **Strongly Typed Models**: Every response is validated using Pydantic, ensuring data integrity and providing full IDE autocompletion support.
* **Async-First Architecture**: Built on top of `httpx` and `asyncio` for maximum concurrency and performance.

---

## 2. Architecture and Design

### Location Resolution Engine

TravelSDK implements a dual-layer resolution strategy:

1. **Local Cache Layer**: Checks the built-in `all_locations.json` for exact matches or codes (IATA/Station codes).
2. **Dynamic Discovery Layer**: If not found locally, the SDK queries the remote API to resolve the area ID and metadata.

### Hierarchical Hub Discovery

A unique feature of TravelSDK is its ability to handle "Hub Resolution". If a user searches for a transport hub in a specific district (which typically lacks its own airport or major station), the SDK recursively queries the parent province to identify the actual gateway (e.g., resolving "Hoan Kiem" to "Hanoi Station").

---

## 3. Installation

TravelSDK requires Python 3.9 or higher.

### Standard Installation

Install the latest stable version from PyPI:

```bash
pip install travel-sdk
```

### Development Installation

Install directly from the GitHub repository for the latest features:

```bash
pip install git+https://github.com/Qhuy204/TravelSDK.git
```

### For Contributors

Clone the repository and install in editable mode with development dependencies:

```bash
git clone https://github.com/Qhuy204/TravelSDK.git
cd TravelSDK
pip install -e ".[dev]"
```

---

## 4. Command Line Interface (CLI)

TravelSDK comes with a powerful CLI tool named `travel-sdk` (exposed as an entry point).

### Basic Usage

```bash
# General help
travel-sdk --help

# Unified search across all modes
travel-sdk search --from "Hanoi" --to "Saigon" --date "2026-05-20"

# Specific mode search
travel-sdk search --from "Hai Phong" --to "Nha Trang" --mode flight

# List available resources
travel-sdk list provinces
travel-sdk list airports
travel-sdk list stations
```

### CLI Flags

* `--verbose`: Enables detailed debugging logs for all HTTP requests.
* `--version`: Displays the current version of the SDK.

---

## 5. Python API Reference

### Initialization

The `TravelClient` is the main entry point. It manages authentication tokens and connection pooling automatically.

```python
from travel import TravelClient

async def main():
    async with TravelClient(timeout=30.0, max_retries=3) as client:
        # Client handles token rotation and retries internally
        pass
```

### Unified Search (`search_all`)

Runs parallel searches across all available transportation modes and returns a consolidated object.

```python
results = await client.search_all(
    from_location="Hanoi",
    to_location="Da Nang",
    date="2026-05-20",
    passengers=1
)

# Accessing specific modes
for train in results.trains:
    print(train.train_number)

# Utility methods
print(results.summary())  # Best for LLM consumption
cheapest = results.cheapest()
```

### Dynamic Location Resolution

The SDK exposes methods to manually resolve locations if you aren't performing an immediate search.

```python
# Returns airport metadata including IATA code and internal location ID
airport_info = await client.resolve_flight_airport_async("Noi Bai")

# Returns train station metadata including station code
station_info = await client.resolve_train_station_async("Cau Giay District")
```

---

## 6. Data Schema (Pydantic Models)

### TrainTicket

| Field              | Type    | Description                                |
| :----------------- | :------ | :----------------------------------------- |
| `train_number`   | `str` | Vehicle identifier (e.g., SE1)             |
| `min_price`      | `int` | Lowest available seat/sleeper price in VND |
| `departure_time` | `str` | Departure time in HH:MM format             |
| `arrival_time`   | `str` | Arrival time in HH:MM format               |
| `seat_available` | `int` | Total number of seats currently available  |

### FlightTicket

| Field             | Type    | Description                            |
| :---------------- | :------ | :------------------------------------- |
| `airline_name`  | `str` | Name of the airline carrier            |
| `flight_number` | `str` | Carriers flight code (e.g., VJ123)     |
| `final_price`   | `int` | Total price including taxes and fees   |
| `baggage_info`  | `str` | Carry-on and checked luggage allowance |

---

## 7. Advanced Usage

### Handling Token Expiration

`TravelClient` automatically monitors token TTL. If a `401 Unauthorized` response is received, it will transparently refresh the token and retry the request without user intervention.

### Logging Configuration

For detailed monitoring, you can enable verbose mode or configure the standard logging library:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
client = TravelClient(verbose=True)
```

---

## 8. Development and Testing

The project uses `pytest` for all verification tests.

```bash
# Run all tests
pytest tests/

# Run specific location resolution tests
python test_hierarchical.py
```

---

## 9. License and Disclaimer

### Disclaimer

This is an **unofficial** SDK and is not affiliated with, endorsed by, or connected to Vexere, VNR (Vietnam Railways), or any specific airline. It utilizes public internal endpoints and is intended for educational and research purposes.

### License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 **Qhuy204**
