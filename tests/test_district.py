import asyncio
import os
import sys

sys.path.append(os.getcwd())

from travel.client import TravelClient
import json

async def test():
    async with TravelClient() as client:
        # Search for a district
        areas = await client.search_areas("Cầu Giấy")
        print("Search results for 'Cầu Giấy':")
        for a in areas:
            print(f"- {a['name']} (ID: {a['id']}, Type: {a['type']}, StateID: {a.get('state_id')})")
        
        if areas:
            # Get detail of the first result
            detail = await client.get_area_details(areas[0]["id"])
            print("\nDetail for the first result:")
            print(json.dumps(detail, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test())
