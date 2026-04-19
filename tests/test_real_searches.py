import pytest
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_real_searches(client):
    """Test real integration search with dynamic locations."""
    # Target date: 30 days from now
    target_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Test 1: Train from Hanoi to Quy Nhon
    print(f"\n[TEST 1] Searching Trains: Hà Nội -> Ga Quy Nhơn (Date: {target_date})")
    trains = await client.search_trains("Hà Nội", "Ga Quy Nhơn", target_date)
    assert isinstance(trains, list)
    print(f"Found {len(trains)} trains.")
    for t in trains[:3]:
        print(f"  - {t.train_number}: {t.departure_time} -> {t.arrival_time} | Price: {t.min_price:,}đ")

    # Test 2: Flight from Cat Bi (Hai Phong) to Cam Ranh (Nha Trang)
    print(f"\n[TEST 2] Searching Flights: Sân Bay Cát Bi -> Sân Bay Cam Ranh (Date: {target_date})")
    flights = await client.search_flights("Sân Bay Cát Bi", "Sân Bay Cam Ranh", target_date)
    assert isinstance(flights, list)
    print(f"Found {len(flights)} flights.")
    for f in flights[:3]:
        airline = f.airline_name or f.airline_code
        price = f.final_price or f.price
        print(f"  - {airline} {f.flight_number}: {f.departure_time} -> {f.arrival_time} | Price: {price:,}đ")

    # Test 3: Train from Binh Dinh to Ninh Hoa
    print(f"\n[TEST 3] Searching Trains: Ga Bình Định -> Ga Ninh Hòa (Date: {target_date})")
    trains_short = await client.search_trains("Ga Bình Định", "Ga Ninh Hòa", target_date)
    assert isinstance(trains_short, list)
    print(f"Found {len(trains_short)} trains.")
