import asyncio
import os
import sys

sys.path.append(os.getcwd())

from travel.client import TravelClient
import json

async def inspect():
    async with TravelClient() as client:
        details = await client.get_area_details(24) # Hanoi
        with open("hanoi_details.json", "w", encoding="utf-8") as f:
            json.dump(details, f, ensure_ascii=False, indent=2)
        print(f"Hanoi children count: {len(details.get('children_areas', []))}")

if __name__ == "__main__":
    asyncio.run(inspect())
