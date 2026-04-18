# TravelSDK Documentation

TravelSDK is a Python library that unifies access to train, bus, and flight search across Vietnam into a single, consistent API. It transforms raw travel data into structured Pydantic models, making it easier to integrate into backend services, data pipelines, or intelligent applications such as chatbots. By abstracting fragmented data sources, TravelSDK helps developers build travel-related features faster and more reliably.

> [!CAUTION]
> **Disclaimer**: This is an unofficial SDK and is not affiliated with or endorsed by Vexere. This project uses publicly accessible endpoints and is intended for educational purposes only. Use at your own risk.

---

## 1. Initialization and Configuration

To get started, initialize the `TravelClient` to manage token authentication and HTTP connections.

### Parameters

```python
from travel import TravelClient

client = TravelClient(
    timeout=30.0,       # Request timeout in seconds
    max_retries=2,      # Number of retries for network issues
    verbose=False       # Enable detailed debug logs
)
```

It is highly recommended to use the client as an async context manager to ensure proper resource cleanup:

```python
async with TravelClient() as client:
    # Perform API calls here
    ...
```

---

## 2. Search Guide

All search functions are asynchronous and support flexible location formats such as city names, IATA codes, or train station codes.

### 2.1 Train Search

Use the `search_trains` function to retrieve data from Vietnam Railways (VNR):

```python
train_tickets = await client.search_trains(
    from_location="Hanoi",
    to_location="Saigon",
    date="2026-04-20",
    passengers=1,
    sort="fare:asc"
)
```

### 2.2 Bus Search

Search through a network of hundreds of bus operators:

```python
bus_tickets = await client.search_buses(
    from_location="Hanoi",
    to_location="Da Nang",
    date="2026-04-20"
)
```

### 2.3 Flight Search

Search for tickets from all domestic airlines:

```python
flight_tickets = await client.search_flights(
    from_location="HAN",
    to_location="SGN",
    date="2026-04-20",
    fare_class="economy"
)
```

### 2.4 Unified Search

The `search_all` function performs simultaneous searches for all three transportation modes:

```python
result = await client.search_all("Hanoi", "Saigon", "2026-04-20")
```

---

## 3. Data Structure

### 3.1 TrainTicket

- `train_number`: Train code (SE1, SE3, etc.)
- `min_price`: Current lowest fare
- `cars`: Detailed carriage info, seat types, and availability
- `utilities`: Amenities like Wifi, Air conditioning, Power outlets
- `images`: Illustration links for train cars

### 3.2 BusTicket

- `operator`: Operator name and code
- `bus_type`: Vehicle type (Limousine, Sleeper, etc.)
- `rating`: Average rating (0-5)
- `pickup_points`, `dropoff_points`: List of stop points with GPS coordinates

### 3.3 FlightTicket

- `airline_name`: Airline company name
- `flight_number`: Flight number
- `airplane_name`: Aircraft model (Airbus, Boeing, etc.)
- `baggage_info`: Carry-on and checked baggage details
- `is_non_stop`: Boolean indicating a direct flight

---

## 4. Utilities and Calendars

### 4.1 Monthly Calendar

Retrieve price and availability for an entire month to help AI suggest the cheapest travel dates:

```python
# Example for train calendar
calendar = await client.get_train_calendar("Hanoi", "Saigon", month=4, year=2026)
```

### 4.2 Location Resolution

The SDK automatically resolves location names to internal IDs, but you can also do it manually:

```python
# Resolve airport by name or IATA code
airport = client.resolve_flight_airport("Tan Son Nhat") 

# Resolve bus region ID
region = client.resolve_bus_region("Ho Chi Minh")
```

---

## 5. Full Code Example

```python
import asyncio
from travel import TravelClient

async def main():
    async with TravelClient() as client:
        # 1. Multi-modal parallel search
        result = await client.search_all("Hanoi", "Saigon", "2026-04-20")
      
        # 2. Extract summary
        summary = result.summary()
        print(f"Summary for AI: {summary}")
      
        # 3. Get cheapest option
        cheapest = result.cheapest()
        print(f"Cheapest: {cheapest.min_price} VND")

        # 4. Fetch flight calendar
        calendar = await client.get_flight_calendar("HAN", "SGN", 5, 2026)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Response Data Samples

### Train

```json
{
  "train_number": "SE9",
  "min_price": 1055000,
  "utilities": ["Air conditioning", "Power outlets"],
  "cars": [{"car_number": "1", "car_type": "Soft Seat"}]
}
```

### Bus

```json
{
  "operator": { "name": "FUTA HA SON" },
  "bus_type": "Limousine 34",
  "rating": 4.8,
  "policies": ["Refundable"]
}
```

### Flight

```json
{
  "airline_name": "Bamboo Airways",
  "airplane_name": "Airbus A320",
  "baggage_info": "7kg carry-on | 10kg checked",
  "policies": ["Refundable", "Changeable"]
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 **Qhuy204**
