import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add current directory to sys.path
sys.path.append(os.getcwd())

from travel.client import TravelClient
import logging

# Configure logging to see the resolution process
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_real_searches():
    # Target date: 30 days from now
    target_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Set encoding for Windows terminal
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    
    async with TravelClient() as client:
        # Test 1: Train from Hanoi to Quy Nhon
        # Quy Nhơn station often has limited trains, let's see.
        print(f"\n[TEST 1] Searching Trains: Hà Nội -> Ga Quy Nhơn (Date: {target_date})")
        trains = await client.search_trains("Hà Nội", "Ga Quy Nhơn", target_date)
        print(f"Found {len(trains)} trains.")
        for t in trains[:3]:
            print(f"  - {t.train_number}: {t.departure_time} -> {t.arrival_time} | Price: {t.min_price:,}đ")

        # Test 2: Flight from Cat Bi (Hai Phong) to Cam Ranh (Nha Trang)
        print(f"\n[TEST 2] Searching Flights: Sân Bay Cát Bi -> Sân Bay Cam Ranh (Date: {target_date})")
        flights = await client.search_flights("Sân Bay Cát Bi", "Sân Bay Cam Ranh", target_date)
        print(f"Found {len(flights)} flights.")
        for f in flights[:3]:
            airline = f.airline_name or f.airline_code
            price = f.final_price or f.price
            print(f"  - {airline} {f.flight_number}: {f.departure_time} -> {f.arrival_time} | Price: {price:,}đ")

        # Test 3: Train from Binh Dinh to Ninh Hoa
        # These are regional stations, checking connectivity.
        print(f"\n[TEST 3] Searching Trains: Ga Bình Định -> Ga Ninh Hòa (Date: {target_date})")
        trains_short = await client.search_trains("Ga Bình Định", "Ga Ninh Hòa", target_date)
        print(f"Found {len(trains_short)} trains.")
        for t in trains_short[:3]:
            print(f"  - {t.train_number}: {t.departure_time} -> {t.arrival_time} | Price: {t.min_price:,}đ")

if __name__ == "__main__":
    asyncio.run(test_real_searches())
