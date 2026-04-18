"""
Debug script: Dump raw flight response from Travel API to understand price schema.
Run: python tests/debug_flight_raw.py
"""
import asyncio
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from travel.client import TravelClient
from travel.constants import FLIGHT_SEARCH_URL, ECONOMY_FARE_CLASSES, ECONOMY_CABIN_CLASSES
from datetime import datetime


async def main():
    async with TravelClient() as client:
        tid = datetime.now().strftime("%H:%M:%S")

        def build_params():
            p = {
                "filter[date]": "2026-04-25",
                "filter[from][0]": "HAN",
                "filter[to][0]": "SGN",
                "filter[quantity]": 1,
                "filter[time_id]": tid,
                "filter[child_infant_count]": 0,
                "filter[infant_count]": 0,
                "filter[is_group_ticket]": 0,
                "filter[show_gom_ve]": 1,
                "filter[page]": 1,
                "filter[pagesize]": 3,
                "page": 1,
                "pagesize": 3,
                "sort": "fare:asc",
                "is_group_ticket": 0,
                "show_gom_ve": 1,
                "time_id": tid,
            }
            for i, fc in enumerate(ECONOMY_FARE_CLASSES):
                p[f"filter[fare_class][{i}]"] = fc
            for i, cc in enumerate(ECONOMY_CABIN_CLASSES):
                p[f"filter[cabin][{i}]"] = cc
            return p

        data = await client._get(FLIGHT_SEARCH_URL, params=build_params())

        # ── ROOT LEVEL KEYS ──
        print("\n=== ROOT KEYS ===")
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  {k}: list({len(v)})")
            elif isinstance(v, dict):
                print(f"  {k}: dict{list(v.keys())[:5]}")
            else:
                print(f"  {k}: {v}")

        # ── FIRST ITEM ALL KEYS ──
        items = data.get("data", [])
        if items:
            print(f"\n=== FIRST FLIGHT ITEM - ALL KEYS ===")
            item = items[0]
            for k, v in item.items():
                if isinstance(v, (dict, list)):
                    print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
                else:
                    print(f"  {k}: {v}")

        # ── PRICE DATA ──
        price_data = data.get("price_data", [])
        print(f"\n=== PRICE DATA (first 3) ===")
        if price_data:
            for pd in price_data[:3]:
                print(f"  {json.dumps(pd, ensure_ascii=False)}")
        else:
            print("  (empty - no price_data key)")

        # ── MIN/MAX PRICE DATA ──
        print(f"\n=== MIN/MAX PRICE DATA ===")
        print(f"  min_price_data: {data.get('min_price_data', '(not found)')}")
        print(f"  max_price_data: {data.get('max_price_data', '(not found)')}")


asyncio.run(main())
