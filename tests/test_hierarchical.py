import asyncio
import os
import sys

# Add the current directory to sys.path so we can import the travel package
sys.path.append(os.getcwd())

from travel.client import TravelClient
import logging

# Configure logging to see the resolution process
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_hierarchical():
    print("Testing Hierarchical Location Resolution (District -> Province Hubs)")
    print("-" * 60)
    
    async with TravelClient() as client:
        # 1. Test Listing provinces from DB
        provinces = client.get_provinces()
        print(f"Loaded {len(provinces)} provinces from local DB.")
        
        # 2. Test District -> Train Station resolution
        # Cầu Giấy is a district in Hanoi. Hanoi has many train stations.
        print("\nResolving Train Station for 'Cầu Giấy' (District):")
        station = await client.resolve_train_station_async("Cầu Giấy")
        if station:
            print(f"Result: {station['name']} (Code: {station['code']}, Dynamic: {station.get('dynamic')})")
        else:
            print("Failed to resolve train station for Cầu Giấy.")
            
        # 3. Test District -> Airport resolution
        # Sân bay Nội Bài is in Sóc Sơn district. Let's try another district in Hanoi.
        print("\nResolving Airport for 'Từ Liêm' (District):")
        airport = await client.resolve_flight_airport_async("Từ Liêm")
        if airport:
            print(f"Result: {airport['name']} (IATA: {airport['iata']}, Dynamic: {airport.get('dynamic')})")
        else:
            print("Failed to resolve airport for Từ Liêm.")

        # 4. Search integration test
        print("\nSearching Trains from 'Cầu Giấy' to 'Vinh' on 2026-04-20:")
        trains = await client.search_trains("Cầu Giấy", "Vinh", "2026-04-20")
        print(f"Found {len(trains)} trains.")
        if trains:
            print(f"Example: {trains[0].train_number} | {trains[0].departure_time} | {trains[0].min_price}đ")

if __name__ == "__main__":
    asyncio.run(test_hierarchical())
