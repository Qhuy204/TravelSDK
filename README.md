
# TravelSDK for Python

[![PyPI version](https://img.shields.io/pypi/v/travel-sdk.svg)](https://pypi.org/project/travel-sdk/) [![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**TravelSDK** là thư viện Python thống nhất để tìm kiếm và so sánh vé tàu, xe khách, và máy bay nội địa Việt Nam theo thời gian thực. SDK trả về dữ liệu Pydantic-validated, async-first, được thiết kế đặc biệt để tích hợp vào **AI Agents** và  **RAG pipelines** .

> ⚠️  **Disclaimer** : Đây là SDK không chính thức, không liên kết với Vexere, VNR hay bất kỳ hãng hàng không nào. Sử dụng cho mục đích nghiên cứu và học tập.

---

## Mục lục

1. [Tính năng nổi bật](#1-tính-năng-nổi-bật)
2. [Kiến trúc](#2-kiến-trúc)
3. [Cài đặt](#3-cài-đặt)
4. [Quickstart — 5 phút chạy được](#4-quickstart--5-phút-chạy-được)
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

## 1. Tính năng nổi bật

| Tính năng                     | Mô tả                                                                                       |
| ------------------------------- | --------------------------------------------------------------------------------------------- |
| **Unified Search**        | Tìm tàu + xe + máy bay trong một lần gọi, chạy song song                               |
| **Hierarchical Location** | Nhập "Quận 1" hay "Cầu Giấy" — SDK tự resolve về hub gần nhất                        |
| **Offline Location DB**   | 63 tỉnh thành, 160+ ga tàu, toàn bộ sân bay nội địa — không cần mạng để lookup |
| **Pydantic Models**       | Mọi response đều validated, IDE autocomplete đầy đủ                                    |
| **Async-first**           | Built trên `httpx`+`asyncio`, phù hợp cho server-side applications                     |
| **Auto Token Refresh**    | Tự động xử lý token expiry, retry on 401/5xx                                             |
| **AI-Ready**              | `summary()`method xuất dict tối ưu cho LLM consumption                                   |

---

## 2. Kiến trúc

```
TravelClient
├── TokenManager          # Bearer token lifecycle (auto-refresh)
├── search_trains()       # → train.py → TrainTicket[]
├── search_buses()        # → bus.py   → BusTicket[]
├── search_flights()      # → flight.py→ FlightTicket[]
├── search_all()          # asyncio.gather() → SearchResult
│
├── Location Resolution (2 layers)
│   ├── Layer 1 - Local DB  (all_locations.json, constants/)
│   └── Layer 2 - Remote API (search_areas → get_area_details)
│       └── Hub Resolution  (District → Province → hub)
│
└── CLI (travel-sdk)      # search + list subcommands
```

### Location Resolution Engine

SDK dùng chiến lược 2 lớp để resolve tên địa điểm:

**Layer 1 — Local Cache (sync, zero-latency):**

* Khớp chính xác với station code (`HNO`, `SGO`) hoặc IATA code (`HAN`, `SGN`)
* Lookup từ `all_locations.json` (bundled, offline)
* Lookup từ `constants/` (các tên phổ biến, alias)

**Layer 2 — Remote API (async, fallback):**

* Gọi `search_areas(query)` → lấy danh sách khu vực khớp
* Ưu tiên type Province > District
* **Hub Resolution** : Nếu district không có hub (ga/sân bay), tự động fetch parent province để tìm hub thực sự

---

## 3. Cài đặt

**Yêu cầu:** Python 3.9+

```bash
# Cài từ PyPI (stable)
pip install travel-sdk

# Cài từ GitHub (latest)
pip install git+https://github.com/Qhuy204/TravelSDK.git

# Cài cho development
git clone https://github.com/Qhuy204/TravelSDK.git
cd TravelSDK
pip install -e ".[dev]"
```

**Dependencies:**

* `httpx >= 0.27` — async HTTP client
* `pydantic >= 2.0` — data validation & serialization

---

## 4. Quickstart — 5 phút chạy được

### Tìm kiếm tất cả phương tiện

```python
import asyncio
from travel import TravelClient

async def main():
    async with TravelClient() as client:
        results = await client.search_all(
            from_location="Hà Nội",
            to_location="Đà Nẵng",
            date="2026-05-20",
            passengers=1,
        )

        print(f"Tàu: {len(results.trains)} chuyến")
        print(f"Xe:  {len(results.buses)} chuyến")
        print(f"Bay: {len(results.flights)} chuyến")

        # Lấy vé rẻ nhất trong tất cả loại
        cheapest = results.cheapest()
        if cheapest:
            print(f"\nRẻ nhất: {cheapest}")

        # Xem top 5 vé rẻ nhất
        for ticket in results.all_tickets[:5]:
            print(ticket)

asyncio.run(main())
```

### Tìm tàu cụ thể

```python
async with TravelClient() as client:
    trains = await client.search_trains(
        from_location="Hà Nội",
        to_location="Sài Gòn",
        date="2026-05-20",
    )

    for t in trains:
        print(f"{t.train_number} | {t.departure_time}→{t.arrival_time} | {t.min_price:,}đ | {t.seat_available} chỗ")
```

### Tìm máy bay

```python
async with TravelClient() as client:
    flights = await client.search_flights(
        from_location="HAN",        # IATA code
        to_location="SGN",
        date="2026-05-20",
        passengers=2,
        fare_class="economy",       # hoặc "business"
    )

    for f in flights:
        print(f"{f.flight_number} | {f.airline_name} | {f.departure_time} | {f.final_price:,}đ | {f.baggage_info}")
```

### Tìm xe khách

```python
async with TravelClient() as client:
    buses = await client.search_buses(
        from_location="Hà Nội",
        to_location="Hải Phòng",
        date="2026-05-20",
    )

    for b in buses:
        print(f"{b.operator.name} | {b.bus_type} | {b.departure_time} | {b.final_price:,}đ | ⭐{b.rating}")
```

---

## 5. Command Line Interface (CLI)

Sau khi cài đặt, SDK expose command `travel-sdk`.

### Tìm kiếm

```bash
# Tìm tất cả phương tiện (mặc định)
travel-sdk search --from "Hà Nội" --to "Đà Nẵng" --date "2026-05-20"

# Tìm theo loại cụ thể
travel-sdk search --from "Hà Nội" --to "Sài Gòn" --date "2026-05-20" --mode train
travel-sdk search --from "Hải Phòng" --to "Đà Lạt"  --date "2026-05-20" --mode flight
travel-sdk search --from "Hà Nội" --to "Hải Phòng"  --date "2026-05-20" --mode bus

# Bật debug log
travel-sdk search --from "Hà Nội" --to "Đà Nẵng" --date "2026-05-20" --verbose
```

**Flags:**

| Flag          | Giá trị                            | Mô tả                                    |
| ------------- | ------------------------------------ | ------------------------------------------ |
| `--from`    | string                               | Địa điểm xuất phát (required)        |
| `--to`      | string                               | Địa điểm đến (required)              |
| `--date`    | `YYYY-MM-DD`                       | Ngày đi (mặc định: hôm nay)          |
| `--mode`    | `all`,`train`,`bus`,`flight` | Loại phương tiện (mặc định:`all`) |
| `--verbose` | flag                                 | Bật DEBUG logging                         |
| `--version` | flag                                 | Hiển thị phiên bản                     |

### Xem danh sách địa điểm

```bash
# Danh sách 63 tỉnh thành
travel-sdk list provinces

# Danh sách sân bay
travel-sdk list airports

# Danh sách ga tàu
travel-sdk list stations
```

---

## 6. Python API Reference

### TravelClient

Entry point chính của SDK. Quản lý token, connection pool, và retry logic.

```python
client = TravelClient(
    timeout=30.0,       # float — HTTP timeout (giây). Mặc định: 30.0
    max_retries=2,      # int   — Số lần retry khi timeout/5xx. Mặc định: 2
    verbose=False,      # bool  — Bật DEBUG logging. Mặc định: False
)
```

**Luôn dùng làm async context manager:**

```python
async with TravelClient() as client:
    # Client tự khởi tạo token và HTTP pool
    ...
# Client tự đóng kết nối khi ra khỏi block
```

> Dùng `TravelClient()` không qua context manager sẽ raise `RuntimeError` khi gọi các search method. Nếu cần dùng standalone, gọi `await client._init_client()` trước.

---

### search_trains

```python
trains: list[TrainTicket] = await client.search_trains(
    from_location: str,           # Địa điểm xuất phát
    to_location: str,             # Địa điểm đến
    date: str,                    # "YYYY-MM-DD"
    passengers: int = 1,          # Số hành khách
    sort: str = "fare:asc",       # Thứ tự sắp xếp
)
```

**`sort` options:** `"fare:asc"` | `"fare:desc"` | `"departure_time:asc"`

**Returns:** `list[TrainTicket]` — danh sách chuyến tàu, đã được sort theo `sort`. Trả về `[]` nếu không tìm thấy hoặc không resolve được địa điểm.

```python
trains = await client.search_trains("Hà Nội", "Đà Nẵng", "2026-05-20")
for t in trains:
    print(f"{t.train_number}: {t.departure_time}→{t.arrival_time} ({t.duration_str})")
    print(f"  Giá từ: {t.min_price:,}đ | Còn: {t.seat_available} chỗ")
    for car in t.cars:
        print(f"  [{car.car_number}] {car.car_type}: {car.min_price:,}đ ({car.total_available} chỗ)")
```

---

### search_buses

```python
buses: list[BusTicket] = await client.search_buses(
    from_location: str | int,     # Tên tỉnh hoặc region ID (int)
    to_location: str | int,       # Tên tỉnh hoặc region ID (int)
    date: str,                    # "YYYY-MM-DD"
    passengers: int = 1,
    sort: str = "fare:asc",
    page: int = 1,                # Pagination
    page_size: int = 20,          # Số kết quả mỗi trang (max 100)
)
```

> **Tip:** Có thể truyền region ID trực tiếp (int) để bỏ qua bước resolve. Xem `travel-sdk list provinces` để lấy danh sách ID.

```python
buses = await client.search_buses("Hà Nội", "Hải Phòng", "2026-05-20")
for b in buses:
    print(f"{b.operator.name} ({b.bus_type}) | {b.departure_time} | {b.final_price:,}đ | ⭐{b.rating}")
    if b.pickup_points:
        print(f"  Đón tại: {b.pickup_points[0].address}")
```

---

### search_flights

```python
flights: list[FlightTicket] = await client.search_flights(
    from_location: str,           # IATA code hoặc tên tỉnh
    to_location: str,             # IATA code hoặc tên tỉnh
    date: str,                    # "YYYY-MM-DD"
    passengers: int = 1,
    fare_class: str = "economy",  # "economy" | "business"
    page: int = 1,
    page_size: int = 20,
    sort: str = "fare:asc",
)
```

```python
flights = await client.search_flights("Hà Nội", "Sài Gòn", "2026-05-20", fare_class="business")
for f in flights:
    print(f"{f.flight_number} ({f.airline_name})")
    print(f"  {f.departure_time}→{f.arrival_time} | {f.duration_minutes // 60}h{f.duration_minutes % 60}m")
    print(f"  {f.final_price:,}đ | {f.baggage_info}")
    if f.utilities:
        print(f"  Tiện ích: {', '.join(f.utilities)}")
```

---

### search_all

Tìm kiếm song song (asyncio.gather) cả 3 phương tiện, trả về `SearchResult`.

```python
result: SearchResult = await client.search_all(
    from_location: str,
    to_location: str,
    date: str,
    passengers: int = 1,
    include_trains: bool = True,   # Có tìm tàu không
    include_buses: bool = True,    # Có tìm xe không
    include_flights: bool = True,  # Có tìm bay không
    page_size: int = 100,          # Số kết quả mỗi loại
)
```

Nếu một loại phương tiện lỗi, các loại còn lại vẫn trả về (lỗi được log ở WARNING).

```python
result = await client.search_all("Hà Nội", "Sài Gòn", "2026-05-20")

# Duyệt từng loại riêng
for t in result.trains:   ...
for b in result.buses:    ...
for f in result.flights:  ...

# Tất cả vé, sắp theo giá tăng dần
for ticket in result.all_tickets:
    print(ticket)

# Vé rẻ nhất toàn bộ
cheapest = result.cheapest()

# Sort theo tiêu chí khác
by_time = result.sort_tickets(result.trains, by="time")
by_airline = result.sort_tickets(result.flights, by="airline")

# Dict tóm tắt (phù hợp làm LLM context)
summary = result.summary()
# {
#   "from": "Hà Nội", "to": "Sài Gòn", "date": "2026-05-20",
#   "train_count": 8, "bus_count": 42, "flight_count": 15,
#   "cheapest_train": 380000, "cheapest_bus": 180000, "cheapest_flight": 990000,
#   "top_train_info": "Tàu SE9 (07:00) - 380000đ",
#   "top_bus_info": "Xe Phương Trang (06:00) - 180000đ",
#   "top_flight_info": "Bay VietJet (06:30) - 990000đ"
# }
```

---

### Calendar APIs

Lấy lịch giá theo tháng để hiển thị trên UI hoặc cho agent lập kế hoạch.

```python
# Lịch giá tàu trong tháng 5/2026
train_calendar: dict = await client.get_train_calendar(
    from_location="Hà Nội",
    to_location="Sài Gòn",
    month=5,
    year=2026,
    passengers=1,
)

# Lịch giá máy bay trong tháng 5/2026
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

Dùng khi cần resolve địa điểm thủ công mà không thực hiện search ngay.

```python
# --- Sync (dùng local DB, zero-latency) ---
station = client.resolve_train_station("Hà Nội")
# {"code": "HNO", "name": "Ga Hà Nội", "location_id": 1, ...}

airport = client.resolve_flight_airport("SGN")
# {"iata": "SGN", "name": "Tân Sơn Nhất", "city": "Hồ Chí Minh", ...}

bus_region = client.resolve_bus_region("Đà Nẵng")
# {"id": 34, "name": "Đà Nẵng", "slug": "da-nang"}

# --- Async (có fallback gọi API + hub resolution) ---
station = await client.resolve_train_station_async("Cầu Giấy")
# Tự resolve: Cầu Giấy (quận) → Hà Nội (tỉnh) → Ga Hà Nội

airport = await client.resolve_flight_airport_async("Quận 1")
# Tự resolve: Quận 1 → TP.HCM → Sân bay Tân Sơn Nhất

# --- Offline DB helpers ---
provinces = client.get_provinces()     # list[dict] — 63 tỉnh thành
airports  = client.get_airports()      # list[dict] — tất cả sân bay
stations  = client.get_train_stations() # list[dict] — tất cả ga tàu
```

---

## 7. Data Schema

### TrainTicket

```python
class TrainTicket(BaseModel):
    type: TicketType               # Luôn là TicketType.TRAIN
    id_index: str                  # ID nội bộ từ API
    train_number: str              # Số hiệu tàu, e.g. "SE9", "TN1"
    operator: Provider             # {"code": "VNR", "name": "Đường sắt Việt Nam"}

    from_code: str                 # Mã ga xuất phát, e.g. "HNO"
    to_code: str                   # Mã ga đến, e.g. "SGO"
    from_name: str                 # Tên ga xuất phát
    to_name: str                   # Tên ga đến

    departure_date: str            # "YYYY-MM-DD"
    departure_time: str            # "HH:MM"
    arrival_date: str              # "YYYY-MM-DD"
    arrival_time: str              # "HH:MM"
    duration_minutes: int          # Thời gian đi (phút)
    duration_str: str              # Property: "32h05m" (tính từ duration_minutes)
    distance_km: int               # Khoảng cách (km)

    min_price: int                 # Giá rẻ nhất (VND)
    seat_available: int            # Tổng số chỗ còn trống
    cars: list[CarInfo]            # Chi tiết từng toa (xem CarInfo bên dưới)

    seat_types: list[str]          # Loại ghế có sẵn, e.g. ["Ngồi mềm", "Nằm khoang 6"]
    utilities: list[str]           # Tiện ích, e.g. ["Điều hòa", "WiFi"]
    policies: list[str]            # Chính sách, e.g. ["Hoàn vé trước 24h"]
    promotions: list[str]          # Khuyến mãi
    baggage_info: str              # Thông tin hành lý
    description: str               # Mô tả chuyến tàu
    images: list[str]              # URL ảnh
    highlights: list[str]          # Điểm nổi bật
```

**CarInfo** (thuộc `TrainTicket.cars`):

```python
class CarInfo(BaseModel):
    car_id: int
    car_number: str                # "1", "2A"
    car_type: str                  # "Ngồi mềm điều hòa", "Nằm khoang 6"
    group_code: str                # "NGM", "NAC", "NAM"
    total_available: int           # Số chỗ còn trống trong toa
    min_price: int                 # Giá thấp nhất trong toa (VND)
    seat_options: list[SeatOption] # Chi tiết từng loại ghế/giường
```

**SeatOption** (thuộc `CarInfo.seat_options`):

```python
class SeatOption(BaseModel):
    code: str                      # Mã nội bộ
    label: str                     # Tên hiển thị, e.g. "Nằm khoang 4 điều hòa"
    seat_class: SeatClass          # Enum: SOFT_SEAT, HARD_SEAT, SLEEPER_6, SLEEPER_4, VIP, ...
    price: int                     # Giá gốc (VND)
    markup_price: Optional[int]    # Giá sau markup
    available: int                 # Số ghế còn lại
```

---

### BusTicket

```python
class BusTicket(BaseModel):
    type: TicketType               # Luôn là TicketType.BUS
    operator: Provider             # {"code": "...", "name": "Phương Trang"}

    from_id: int                   # Bus region ID điểm đi
    to_id: int                     # Bus region ID điểm đến
    from_name: str
    to_name: str

    departure_date: str            # "YYYY-MM-DD"
    departure_time: str            # "HH:MM"
    arrival_time: str              # "HH:MM"
    duration_minutes: int

    bus_type: str                  # "Limousine", "Giường nằm 40 chỗ", "Sleeper VIP"
    seat_available: int

    price: int                     # Giá gốc (VND)
    final_price: int               # Giá sau giảm (VND)

    pickup_points: list[PointInfo] # Điểm đón khách
    dropoff_points: list[PointInfo]# Điểm trả khách

    rating: float                  # Đánh giá trung bình (0.0–5.0)
    reviews: int                   # Số lượt đánh giá

    utilities: list[str]           # Tiện ích, e.g. ["WiFi", "Điều hòa", "Sạc điện"]
    policies: list[str]
    promotions: list[str]
    baggage_info: str
    description: str
```

**PointInfo** (thuộc `BusTicket.pickup_points` / `dropoff_points`):

```python
class PointInfo(BaseModel):
    name: str                      # Tên điểm đón/trả
    address: str                   # Địa chỉ đầy đủ
    time_offset_minutes: int       # Offset so với giờ khởi hành
    lat: float                     # Vĩ độ
    lon: float                     # Kinh độ
```

---

### FlightTicket

```python
class FlightTicket(BaseModel):
    type: TicketType               # Luôn là TicketType.FLIGHT
    id_index: str                  # ID nội bộ

    airline_code: str              # "VJ", "VN", "QH", "BL"
    airline_name: str              # "VietJet Air", "Vietnam Airlines"
    flight_number: str             # "VJ123", "VN204"
    cabin: str                     # "Economy", "Business"
    airplane_name: str             # "Airbus A321", "Boeing 787"
    is_non_stop: bool              # True nếu bay thẳng

    from_iata: str                 # "HAN", "DAD", "SGN"
    to_iata: str
    from_name: str
    to_name: str

    departure_date: str            # "YYYY-MM-DD"
    departure_time: str            # "HH:MM"
    arrival_time: str              # "HH:MM"
    duration_minutes: int

    price: int                     # Giá chưa thuế (VND)
    final_price: int               # Giá đã gồm thuế, phí (VND)

    baggage_info: str              # "7kg xách tay + 20kg ký gửi"
    utilities: list[str]           # Tiện ích đi kèm
    policies: list[str]            # Chính sách đổi/hoàn vé
    promotions: list[str]
    description: str
```

---

### SearchResult

Object trả về từ `search_all()`.

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
    all_tickets                    # property: tất cả vé sắp theo giá tăng dần
    cheapest()                     # → ticket rẻ nhất
    summary()                      # → dict tóm tắt (xem bên dưới)
    sort_tickets(tickets, by, reverse)  # sort theo "price", "time", "airline"/"operator"
```

**`summary()` output:**

```python
{
    "from": "Hà Nội",
    "to": "Sài Gòn",
    "date": "2026-05-20",
    "train_count": 8,
    "bus_count": 42,
    "flight_count": 15,
    "cheapest_train": 380000,     # VND, hoặc None nếu không có
    "cheapest_bus": 180000,
    "cheapest_flight": 990000,
    "top_train_info": "Tàu SE9 (07:00) - 380000đ",
    "top_bus_info": "Xe Phương Trang (06:00) - 180000đ",
    "top_flight_info": "Bay VietJet (06:30) - 990000đ"
}
```

---

## 8. Location Format

SDK chấp nhận nhiều định dạng địa điểm:

| Input             | Loại          | Ví dụ                                                 |
| ----------------- | -------------- | ------------------------------------------------------- |
| Tên tỉnh/thành | Fuzzy match    | `"Hà Nội"`,`"hanoi"`,`"Sài Gòn"`,`"tp hcm"` |
| Alias phổ biến  | Mapping cứng  | `"hn"`,`"hcm"`,`"tphcm"`,`"sgn"`                |
| IATA code         | Chính xác    | `"HAN"`,`"SGN"`,`"DAD"`,`"HUI"`                 |
| Mã ga tàu       | Chính xác    | `"HNO"`,`"SGO"`,`"DAN"`                           |
| Tên quận/huyện | Hub resolution | `"Quận 1"`,`"Cầu Giấy"`,`"Hoàn Kiếm"`        |
| Region ID (bus)   | Direct (int)   | `1`,`34`,`2`                                      |

**Danh sách IATA code sân bay chính:**

| Sân bay        | IATA    | Tỉnh                   |
| --------------- | ------- | ----------------------- |
| Nội Bài       | `HAN` | Hà Nội                |
| Tân Sơn Nhất | `SGN` | TP.HCM                  |
| Đà Nẵng      | `DAD` | Đà Nẵng              |
| Cam Ranh        | `CXR` | Khánh Hòa (Nha Trang) |
| Phú Quốc      | `PQC` | Kiên Giang             |
| Cát Bi         | `HPH` | Hải Phòng             |
| Phú Bài       | `HUI` | Thừa Thiên Huế       |
| Liên Khương  | `DLI` | Lâm Đồng (Đà Lạt) |
| Cần Thơ       | `VCA` | Cần Thơ               |

**Danh sách mã ga tàu chính:**

| Ga         | Code    |
| ---------- | ------- |
| Hà Nội   | `HNO` |
| Sài Gòn  | `SGO` |
| Đà Nẵng | `DAN` |
| Huế       | `HUE` |
| Nha Trang  | `NTR` |

Xem đầy đủ: `travel-sdk list stations` hoặc `travel-sdk list airports`

---

## 9. Error Handling

### Không tìm thấy địa điểm

SDK trả về `[]` (list rỗng) thay vì raise exception khi không resolve được địa điểm. Kiểm tra log để debug:

```python
import logging
logging.basicConfig(level=logging.INFO)

async with TravelClient() as client:
    trains = await client.search_trains("XYZ không tồn tại", "Đà Nẵng", "2026-05-20")
    if not trains:
        print("Không tìm thấy tàu — kiểm tra tên địa điểm")
```

### Network errors & retry

`TravelClient` tự động retry khi gặp:

* `httpx.TimeoutException` → retry với exponential backoff (1s, 2s)
* HTTP 5xx → retry với exponential backoff
* HTTP 401 → tự refresh token rồi retry

Sau khi hết retry, exception sẽ được raise để ứng dụng xử lý:

```python
import httpx

try:
    async with TravelClient(timeout=10.0, max_retries=3) as client:
        trains = await client.search_trains("Hà Nội", "Đà Nẵng", "2026-05-20")
except httpx.TimeoutException:
    print("Request timeout sau 10 giây")
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
except Exception as e:
    print(f"Lỗi không xác định: {e}")
```

### search_all partial failure

Nếu một phương tiện lỗi trong `search_all`, phương tiện còn lại vẫn trả về:

```python
result = await client.search_all("Hà Nội", "Sài Gòn", "2026-05-20")
# Nếu search_flights lỗi → result.flights = [], trains và buses vẫn có data
# Lỗi được log ở WARNING level
```

---

## 10. AI Agent / RAG Integration

SDK được tối ưu cho việc tích hợp vào LLM agents. Pattern khuyên dùng:

### Dùng `summary()` làm LLM context

```python
async def search_travel_for_agent(origin: str, destination: str, date: str) -> str:
    """Tool function cho LLM agent."""
    async with TravelClient() as client:
        result = await client.search_all(origin, destination, date)
        summary = result.summary()

    # Format cho LLM
    return f"""
Kết quả tìm kiếm: {summary['from']} → {summary['to']} ngày {summary['date']}

Máy bay: {summary['flight_count']} chuyến, rẻ nhất {summary['cheapest_flight']:,}đ
{summary.get('top_flight_info', 'Không có')}

Tàu hỏa: {summary['train_count']} chuyến, rẻ nhất {summary['cheapest_train']:,}đ
{summary.get('top_train_info', 'Không có')}

Xe khách: {summary['bus_count']} chuyến, rẻ nhất {summary['cheapest_bus']:,}đ
{summary.get('top_bus_info', 'Không có')}
""".strip()
```

### Tool definition cho OpenAI / Claude function calling

```python
travel_search_tool = {
    "name": "search_travel",
    "description": "Tìm kiếm vé tàu, xe, máy bay nội địa Việt Nam theo thời gian thực.",
    "parameters": {
        "type": "object",
        "properties": {
            "from_location": {
                "type": "string",
                "description": "Điểm xuất phát (tên tỉnh, IATA code, hoặc mã ga)"
            },
            "to_location": {
                "type": "string",
                "description": "Điểm đến"
            },
            "date": {
                "type": "string",
                "description": "Ngày đi, định dạng YYYY-MM-DD"
            },
            "mode": {
                "type": "string",
                "enum": ["all", "train", "bus", "flight"],
                "description": "Loại phương tiện cần tìm"
            }
        },
        "required": ["from_location", "to_location", "date"]
    }
}
```

### Xử lý trong agent

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

### Cài dev dependencies

```bash
pip install -e ".[dev]"
# Bao gồm: pytest, pytest-asyncio, python-dotenv
```

### Chạy tests

```bash
# Tất cả tests
pytest tests/

# Tests location resolution (offline, không cần API)
pytest tests/test_locations.py

# Tests models (offline)
pytest tests/test_models.py

# Tests live API (cần internet)
pytest tests/test_live_api.py -v

# Tests hierarchical resolution
python test_hierarchical.py

# Tests với log chi tiết
pytest tests/ -v --log-cli-level=DEBUG
```

### Cấu trúc project

```
TravelSDK/
├── travel/                     # Package chính
│   ├── __init__.py             # Public API exports
│   ├── client.py               # TravelClient entry point
│   ├── auth.py                 # TokenManager
│   ├── flight.py               # Flight search logic
│   ├── train.py                # Train search logic
│   ├── bus.py                  # Bus search logic
│   ├── locations.py            # Location resolution engine
│   ├── cli.py                  # CLI entry point
│   ├── constants/              # URL, mã tỉnh thành, mã ga
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
│       └── all_locations.json  # Offline location DB
├── tests/                      # Unit & integration tests
├── examples/                   # Ví dụ sử dụng
│   └── search_demo.py
├── pyproject.toml
└── README.md
```

---

## 12. Changelog

### v0.1.3 (2026-04-19)

* **Smart Fuzzy Matching**: Tích hợp `difflib.get_close_matches` cho cả 3 chế độ — Train, Flight, Bus. Người dùng có thể nhập `hnoi`, `sgn`, `hcm` và SDK tự resolve đúng.
* **CLI Bug Fix**: Sửa `AttributeError` khi hiển thị kết quả bus (`b.operator_name` → `b.operator.name`).
* **Dynamic Versioning**: `--version` flag đọc từ package metadata thay vì hardcode.
* **Accurate `summary()`**: Dùng `min()` thay cho `[0]` để đảm bảo giá hiển thị luôn là giá rẻ nhất thực sự.
* **Auth Stability**: Refactor `TokenManager._acquire()` sang vòng lặp iterative, loại bỏ recursion gây `RuntimeError: Event loop is closed`.
* **PEP 561**: Thêm `travel/py.typed` marker để IDE nhận đầy đủ type hints.
* **Test Suite**: Chuyển đổi toàn bộ test scripts sang `pytest-asyncio` chuẩn. Thêm `tests/conftest.py` và đạt 35/35 tests passed.
* **Structure**: Di chuyển test files vào `tests/`, thêm `scratch/` vào `.gitignore`.

### v0.1.2 (2026-04-19)

* Thêm `include_trains/buses/flights` flags cho `search_all`
* Cải thiện hierarchical hub resolution cho district-level queries
* CLI: thêm `--mode` flag và `--list`/`--search` alias
* Fix PyPI version conflict bằng cách bump version

### v0.1.1 (2026-04-19)

* Fix token invalidation khi nhận 401
* Thêm exponential backoff cho retry
* Đăng ký CLI entry point `travel-sdk`

### v0.1.0 (2026-04-18)

* Initial release
* Unified search API cho tàu, xe, máy bay
* Offline location database (63 tỉnh, 160+ ga, toàn bộ sân bay nội địa)
* Hierarchical location resolution (District → Province Hub)

---

## License

MIT License — Copyright (c) 2026 [Qhuy204](https://github.com/Qhuy204)

> SDK này là unofficial và không được endorsement bởi Vexere, VNR, hay bất kỳ hãng hàng không nào. Chỉ dùng cho mục đích nghiên cứu và học tập.
>
