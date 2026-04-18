"""
Demo script for TravelSDK - Search all transportation from Hà Nội to Sài Gòn.
Run: python examples/search_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Fix Windows console encoding for Vietnamese characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add parent dir to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from travel import TravelClient

logging.basicConfig(level=logging.INFO)


def format_vnd(price: int) -> str:
    """Format VND price with thousands separator."""
    return f"{price:,.0f}đ"


async def main():
    print("=" * 60)
    print("   TravelSDK - Search Demo (Hà Nội → Sài Gòn)")
    print("=" * 60)

    date = "2026-04-20"
    from_city = "Hà Nội"
    to_city = "Sài Gòn"

    async with TravelClient(verbose=False) as client:

        # ── Search all simultaneously ──────────────────────────────────────
        print(f"\n🔍 Searching {from_city} → {to_city} on {date}...")
        results = await client.search_all(from_city, to_city, date)

        print(f"\n📊 Summary:")
        summary = results.summary()
        print(f"  🚂 Trains: {summary['train_count']} chuyến, "
              f"từ {format_vnd(summary['cheapest_train'] or 0)}")
        print(f"  🚌 Buses:  {summary['bus_count']} chuyến, "
              f"từ {format_vnd(summary['cheapest_bus'] or 0)}")
        print(f"  ✈️  Flights: {summary['flight_count']} chuyến, "
              f"từ {format_vnd(summary['cheapest_flight'] or 0)}")

        # ── Train details ──────────────────────────────────────────────────
        if results.trains:
            print(f"\n🚂 Top 5 chuyến tàu rẻ nhất:")
            print(f"  {'Tàu':<8} {'Giờ khởi hành':<16} {'Giá thấp nhất':<16} {'Còn chỗ'}")
            print("  " + "-" * 55)
            for t in results.trains[:5]:
                print(f"  {t.train_number:<8} {t.departure_time:<16} "
                      f"{format_vnd(t.min_price):<16} {t.seat_available} chỗ")

                # Show seat options for first train
                if t == results.trains[0] and t.cars:
                    print(f"\n    Chi tiết toa xe của {t.train_number}:")
                    seen_groups = set()
                    for car in t.cars:
                        if car.group_code not in seen_groups:
                            seen_groups.add(car.group_code)
                            for opt in car.seat_options[:1]:
                                print(f"      - {opt.label}: {format_vnd(opt.price)} "
                                      f"(còn {opt.available} chỗ)")

        # ── Flight details ─────────────────────────────────────────────────
        if results.flights:
            print(f"\n✈️  Top 5 chuyến bay rẻ nhất:")
            print(f"  {'Hãng':<8} {'Chuyến bay':<12} {'Giờ khởi hành':<16} {'Giá (VND)'}")
            print("  " + "-" * 55)
            for f in results.flights[:5]:
                print(f"  {f.airline_name:<8} {f.flight_number:<12} "
                      f"{f.departure_time:<16} {format_vnd(f.final_price)}")

        # ── Bus details ────────────────────────────────────────────────────
        if results.buses:
            print(f"\n🚌 Top 5 chuyến xe rẻ nhất:")
            print(f"  {'Hãng xe':<20} {'Giờ khởi hành':<16} {'Loại xe':<16} {'Giá'}")
            print("  " + "-" * 65)
            for b in results.buses[:5]:
                print(f"  {b.operator.name[:18]:<20} {b.departure_time:<16} "
                      f"{b.bus_type[:14]:<16} {format_vnd(b.final_price)}")

        # ── Cheapest overall ───────────────────────────────────────────────
        cheapest = results.cheapest()
        if cheapest:
            print(f"\n🏆 Lựa chọn rẻ nhất:")
            print(f"  Loại: {cheapest.type.value}")
            if hasattr(cheapest, 'train_number'):
                print(f"  Tàu: {cheapest.train_number} | {cheapest.departure_time} | "
                      f"{format_vnd(cheapest.min_price)}")
            elif hasattr(cheapest, 'flight_number'):
                print(f"  Bay: {cheapest.flight_number} | {cheapest.departure_time} | "
                      f"{format_vnd(cheapest.final_price)}")
            else:
                print(f"  Xe: {cheapest.operator.name} | {cheapest.departure_time} | "
                      f"{format_vnd(cheapest.final_price)}")

        # ── Train Calendar ────────────────────────────────────────────────
        print(f"\n📅 Lịch giá tàu tháng 4/2026:")
        calendar = await client.get_train_calendar("Hà Nội", "Sài Gòn", month=4, year=2026)
        if calendar and "data" in calendar:
            cal_data = calendar["data"]
            # May be a list or a dict depending on API version
            if isinstance(cal_data, list):
                for entry in cal_data[:5]:
                    date_key = entry.get("date", "?")
                    price = entry.get("min_price", entry.get("minPrice", 0))
                    print(f"  {date_key}: {format_vnd(price)}")
            elif isinstance(cal_data, dict):
                for date_key, info in list(cal_data.items())[:5]:
                    price = info.get("min_price", info.get("minPrice", 0)) if isinstance(info, dict) else info
                    print(f"  {date_key}: {format_vnd(price)}")
        else:
            print("  (No calendar data available)")

    print("\n✅ Demo hoàn tất!")


if __name__ == "__main__":
    asyncio.run(main())
