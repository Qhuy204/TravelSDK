import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from travel.client import TravelClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_specific_locations():
    test_cases = [
        ("train", "Ga Quy Nhơn"),
        ("train", "Ga Bình Định"),
        ("flight", "Sân Bay Cát Bi"),
        ("flight", "Sân Bay Cam Ranh"),
        ("train", "Ga Viên Yên"), # Potential typo for Ga Yên Viên
        ("train", "Ga Ninh Hòa"),
    ]
    
    print(f"{'Type':<10} | {'Query':<20} | {'Resolved Name':<25} | {'ID/Code'}")
    print("-" * 75)
    
    async with TravelClient() as client:
        for loc_type, query in test_cases:
            result = None
            if loc_type == "train":
                result = await client.resolve_train_station_async(query)
                name = result['name'] if result else "N/A"
                code = result['code'] if result else "N/A"
            else:
                result = await client.resolve_flight_airport_async(query)
                name = result['name'] if result else "N/A"
                code = result['iata'] if result else "N/A"
            
            print(f"{loc_type:<10} | {query:<20} | {name:<25} | {code}")

if __name__ == "__main__":
    # Ensure current console supports UTF-8 for printing results
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        
    asyncio.run(test_specific_locations())
