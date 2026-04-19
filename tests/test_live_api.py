import pytest
import json
import logging

# Disable excessive logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("travel").setLevel(logging.WARNING)

from travel.locations import resolve_train_station, resolve_flight_airport, resolve_bus_region

# ─── Config ───────────────────────────────────────────────────────────────────
TEST_DATE = "2026-04-20"
FROM_CITY = "Hà Nội"
TO_CITY   = "Sài Gòn"

PASS = "[OK]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"


def hr(title: str = ""):
    if title:
        print(f"\n{'─'*20} {title} {'─'*20}")
    else:
        print("─" * 50)


def ok(msg: str):
    print(f"  {PASS} {msg}")


def fail(msg: str):
    print(f"  {FAIL} {msg}")


def warn(msg: str):
    print(f"  {SKIP} {msg}")


def dump(label: str, obj, max_keys: int = 10):
    """Pretty print top-level keys of a dict/list."""
    if isinstance(obj, dict):
        keys = list(obj.keys())[:max_keys]
        print(f"     Keys: {keys}")
    elif isinstance(obj, list):
        print(f"     [{len(obj)} items]  first: {json.dumps(obj[0], ensure_ascii=False)[:120] if obj else 'empty'}...")


# ─── Test Groups ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth(client):
    hr("1. Authentication")
    try:
        # Token should already be acquired during __aenter__
        bearer = client._token_manager.bearer_header
        ok(f"Token acquired: {bearer[:40]}...")
        ok(f"Token expired: {client._token_manager.is_expired}")
    except Exception as e:
        fail(f"Auth error: {e}")


@pytest.mark.asyncio
async def test_location_resolver():
    hr("2. Location Resolver")

    # Train
    cases = [
        ("HNO", "train"),
        ("Hà Nội", "train"),
        ("hcm", "train"),
        ("HAN", "flight"),
        ("Sài Gòn", "flight"),
        ("tphcm", "flight"),
        ("Hà Nội", "bus"),
        ("ho chi minh", "bus"),
        ("Đà Nẵng", "bus"),
    ]
    for query, mode in cases:
        if mode == "train":
            result = resolve_train_station(query)
            if result:
                ok(f"Train '{query}' → {result['code']} ({result['name']})")
            else:
                fail(f"Train '{query}' → NOT FOUND")

        elif mode == "flight":
            result = resolve_flight_airport(query)
            if result:
                ok(f"Flight '{query}' → {result['iata']} ({result.get('city','')})")
            else:
                fail(f"Flight '{query}' → NOT FOUND")

        elif mode == "bus":
            result = resolve_bus_region(query)
            if result:
                ok(f"Bus   '{query}' → ID {result['id']} ({result['name']})")
            else:
                fail(f"Bus   '{query}' → NOT FOUND")


@pytest.mark.asyncio
async def test_train_search(client):
    hr("3. Train Search (live)")
    print(f"  Route: {FROM_CITY} → {TO_CITY}  |  Date: {TEST_DATE}")
    try:
        trains = await client.search_trains(FROM_CITY, TO_CITY, TEST_DATE)
        if trains:
            ok(f"Found {len(trains)} trains")
            print()
            print(f"  {'Tàu':<8} {'Khởi hành':<12} {'Đến ngày':<12} {'Giá min (VND)':<18} {'Chỗ còn'}")
            print("  " + "─" * 65)
            for t in trains:
                print(f"  {t.train_number:<8} {t.departure_time:<12} {t.arrival_date:<12} "
                      f"{t.min_price:>15,}  {t.seat_available:>4} chỗ")

            # Detail test on first train
            first = trains[0]
            if first.promotions:
                print(f"\n  [Chương trình Khuyến Mãi]")
                for p in first.promotions:
                    print(f"    - {p}")
            if first.policies:
                print(f"\n  [Chính sách & Khuyến Mãi]")
                for p in first.policies:
                    print(f"    - {p}")
            if first.seat_types:
                print(f"\n  [Các loại ghế]")
                for st in first.seat_types:
                    print(f"    - {st}")
            if first.utilities:
                print(f"\n  [Tiện ích]")
                for u in first.utilities:
                    print(f"    - {u}")
            if first.highlights:
                print(f"\n  [Điểm nổi bật]")
                for h in first.highlights:
                    print(f"    - {h}")
            if first.images:
                print(f"\n  [Hình ảnh]")
                for img in first.images:
                    print(f"    • {img}")
                    
            print(f"\n  [Chi tiết toa xe của tàu {first.train_number}]")
            for car in first.cars[:3]:
                print(f"     Toa {car.car_number} ({car.car_type}): còn {car.total_available} ghế | min {car.min_price:,}đ")
                for opt in car.seat_options[:2]:
                    print(f"       • {opt.label}: {opt.price:,}đ ({opt.available} chỗ)")
        else:
            warn("No trains found (may be no service on this date)")
    except Exception as e:
        fail(f"Train search error: {e}")
        import traceback; traceback.print_exc()


@pytest.mark.asyncio
async def test_flight_search(client):
    hr("4. Flight Search (live)")
    print(f"  Route: HAN → SGN  |  Date: {TEST_DATE}")
    try:
        flights = await client.search_flights("HAN", "SGN", TEST_DATE, page_size=100)
        if flights:
            ok(f"Found {len(flights)} flights")
            print()
            print(f"  {'Hãng':<20} {'Chuyến':<8} {'Khởi hành':<12} {'Thời gian bay':<15} {'Máy bay/Loại':<15} {'Giá (VND)'}")
            print("  " + "─" * 90)
            for f in flights:
                price_str = f"{f.final_price:>12,}" if f.final_price else "  (chưa có)"
                duration_hrs = f.duration_minutes // 60
                duration_mins = f.duration_minutes % 60
                duration_str = f"{duration_hrs}h{duration_mins}m"
                print(f"  {f.airline_name[:18]:<20} {f.flight_number:<8} "
                      f"{f.departure_time:<12} {duration_str:<15} {f.description[:15]:<15} {price_str}")
                
            first = flights[0]
            print(f"\n  [Thông tin chuyến bay {first.flight_number}]")
            print(f"    - Loại chuyến: {'Bay thẳng' if first.is_non_stop else 'Có chặng dừng'}")
            print(f"    - Máy bay: {first.airplane_name}")
            print(f"    - Hành lý: {first.baggage_info}")
            if first.utilities:
                print(f"    - Tiện ích: {', '.join(first.utilities)}")
            if first.policies:
                print(f"    - Chính sách: {', '.join(first.policies)}")
            if first.promotions:
                print(f"    - Khuyến mãi: {', '.join(first.promotions)}")
        else:
            warn("No flights found")
    except Exception as e:
        fail(f"Flight search error: {e}")
        import traceback; traceback.print_exc()


@pytest.mark.asyncio
async def test_bus_search(client):
    hr("5. Bus Search (live)")
    # Use Hanoi → Da Nang (shorter route, more likely to have buses)
    from_bus = "Hà Nội"
    to_bus   = "Đà Nẵng"
    print(f"  Route: {from_bus} → {to_bus}  |  Date: {TEST_DATE}")
    try:
        buses = await client.search_buses(from_bus, to_bus, TEST_DATE, page_size=100)
        if buses:
            ok(f"Found {len(buses)} buses")
            print()
            print(f"  {'Nhà xe':<20} {'Khởi hành':<12} {'Đến nơi':<10} {'Loại xe':<25} {'Chỗ trống':<10} {'Giá (VND)'}")
            print("  " + "─" * 95)
            for b_ticket in buses:
                bus_type_disp = b_ticket.bus_type if b_ticket.bus_type else "(Không rõ)"
                price_str = f"{b_ticket.final_price:>12,}" if b_ticket.final_price else "  (chưa có)"
                print(f"  {b_ticket.operator.name[:18]:<20} {b_ticket.departure_time:<12} {b_ticket.arrival_time:<10} "
                      f"{bus_type_disp[:23]:<25} {b_ticket.seat_available:<10} {price_str}")

            first = buses[0]
            print(f"\n  [Thông tin xe {first.operator.name}]")
            print(f"    - Đánh giá: {first.rating}/5 ({first.reviews} lượt đánh giá)")
            print(f"    - Loại xe: {first.bus_type}")
            if first.utilities:
                print(f"    - Tiện ích: {', '.join(first.utilities)}")
            if first.policies:
                print(f"    - Chính sách: {', '.join(first.policies)}")
            if first.promotions:
                print(f"    - Khuyến mãi: {', '.join(first.promotions)}")
                
            if first.pickup_points:
                print(f"\n  [Điểm Đón]")
                for p in first.pickup_points[:3]:
                    addr = p.address or p.name
                    print(f"    • {addr} (Tọa độ: {p.lat}, {p.lon})")
            if first.dropoff_points:
                print(f"\n  [Điểm Trả]")
                for p in first.dropoff_points[:3]:
                    addr = p.address or p.name
                    print(f"    • {addr} (Tọa độ: {p.lat}, {p.lon})")
        else:
            warn(f"No buses found for {from_bus}→{to_bus} on {TEST_DATE}")
    except Exception as e:
        fail(f"Bus search error: {e}")
        import traceback; traceback.print_exc()


@pytest.mark.asyncio
async def test_train_calendar(client):
    hr("6. Train Calendar (live)")
    print(f"  Route: {FROM_CITY} → {TO_CITY}  |  Tháng 4/2026")
    try:
        cal = await client.get_train_calendar(FROM_CITY, TO_CITY, month=4, year=2026)
        if cal:
            data = cal.get("data", {})
            if isinstance(data, list) and data:
                data = data[0]
            grouped = data.get("grouped_by_date", {}) if isinstance(data, dict) else {}
            if grouped:
                ok(f"Calendar returned {len(grouped)} dates")
                print(f"  [5 ngày đầu]")
                for i, (date_str, info) in enumerate(list(grouped.items())):
                    count = info.get("count", 0)
                    min_price = info.get("min_fare", info.get("min_price", "?"))
                    print(f"     {date_str}: {f'{min_price:,}đ' if isinstance(min_price, int) else min_price}  |  {count} chuyến")
            else:
                warn("Empty train calendar entries")
        else:
            warn("Empty calendar response")
    except Exception as e:
        fail(f"Calendar error: {e}")
        import traceback; traceback.print_exc()


@pytest.mark.asyncio
async def test_flight_calendar(client):
    hr("7. Flight Calendar (live)")
    print(f"  Route: HAN → SGN  |  Tháng 4/2026")
    try:
        cal = await client.get_flight_calendar("HAN", "SGN", month=4, year=2026)
        if cal:
            data = cal.get("data", {})
            if isinstance(data, list) and data:
                data = data[0]
            grouped = data.get("grouped_by_date", {}) if isinstance(data, dict) else {}
            if grouped:
                ok(f"Calendar returned {len(grouped)} dates")
                print(f"  [5 ngày đầu]")
                for i, (date_str, info) in enumerate(list(grouped.items())[:5]):
                    count = info.get("count", 0)
                    min_price = info.get("min_fare", info.get("min_price", "?"))
                    print(f"     {date_str}: {f'{min_price:,}đ' if isinstance(min_price, int) else min_price}  |  {count} chuyến")
            else:
                warn(f"Empty flight calendar (Grouped: {len(grouped)})")
        else:
            warn("Empty flight calendar response")
    except Exception as e:
        fail(f"Calendar error: {e}")
        import traceback; traceback.print_exc()


@pytest.mark.asyncio
async def test_search_all(client):
    hr("8. search_all() - Parallel Search")
    print(f"  Route: {FROM_CITY} → {TO_CITY}  |  Date: {TEST_DATE}")
    try:
        import time
        t0 = time.time()
        results = await client.search_all(FROM_CITY, TO_CITY, TEST_DATE, page_size=100)
        elapsed = time.time() - t0

        ok(f"Completed in {elapsed:.2f}s")
        summary = results.summary()
        print(f"\n  Summary:")
        if summary.get('top_train_info'):
            print(f"     Trains:   {summary['train_count']} chuyến  | Rẻ nhất: {summary['top_train_info']}")
        else:
            print(f"     Trains:   {summary['train_count']} chuyến")
            
        if summary.get('top_bus_info'):
            print(f"     Buses:    {summary['bus_count']} chuyến  | Rẻ nhất: {summary['top_bus_info']}")
        else:
            print(f"     Buses:    {summary['bus_count']} chuyến")
            
        if summary.get('top_flight_info'):
            print(f"     Flights:  {summary['flight_count']} chuyến | Rẻ nhất: {summary['top_flight_info']}")
        else:
            print(f"     Flights:  {summary['flight_count']} chuyến")

        cheapest = results.cheapest()
        if cheapest:
            print(f"\n  Overall Rẻ nhất: [{cheapest.type.value.upper()}] ", end="")
            if hasattr(cheapest, 'train_number'):
                print(f"Tàu {cheapest.train_number} lúc {cheapest.departure_time} — {cheapest.min_price:,}đ")
            elif hasattr(cheapest, 'flight_number'):
                print(f"Bay {cheapest.flight_number} lúc {cheapest.departure_time} — {cheapest.final_price:,}đ")
            else:
                print(f"Xe {cheapest.operator.name} lúc {cheapest.departure_time} — {cheapest.final_price:,}đ")
    except Exception as e:
        fail(f"search_all error: {e}")
        import traceback; traceback.print_exc()


@pytest.mark.asyncio
async def test_token_refresh(client):
    hr("9. Token Auto-Refresh")
    try:
        # Force invalidate and re-acquire
        client._token_manager.invalidate()
        ok("Token invalidated")
        bearer = await client._token_manager.ensure_token(client._http_client)
        ok(f"Token re-acquired: {bearer[:40]}...")
    except Exception as e:
        fail(f"Token refresh error: {e}")


# Standalone runner logic removed in favor of pytest.
