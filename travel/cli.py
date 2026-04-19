import argparse
import asyncio
import sys
import json
import importlib.metadata
from datetime import datetime
from travel.client import TravelClient
import logging

def format_price(amount: int) -> str:
    if not amount: return "N/A"
    return f"{amount:,}đ"

async def run_search(args):
    """Execution logic for the 'search' subcommand."""
    print(f"Searching {args.mode} from {args.origin} to {args.destination} on {args.date}...")
    
    async with TravelClient(verbose=args.verbose) as client:
        if args.mode == "train":
            results = await client.search_trains(args.origin, args.destination, args.date)
            if not results:
                print("No trains found.")
                return
            print(f"\n{'Train':<6} | {'Departure':<10} | {'Arrival':<10} | {'Min Price':<12} | {'Available'}")
            print("-" * 60)
            for t in results:
                print(f"{t.train_number:<6} | {t.departure_time:<10} | {t.arrival_time:<10} | {format_price(t.min_price):<12} | {t.seat_available}")
        
        elif args.mode == "flight":
            results = await client.search_flights(args.origin, args.destination, args.date)
            if not results:
                print("No flights found.")
                return
            print(f"\n{'Flight':<10} | {'Airline':<20} | {'Dep Time':<10} | {'Price':<12}")
            print("-" * 60)
            for f in results:
                airline = f.airline_name or f.airline_code
                print(f"{f.flight_number:<10} | {airline:<20} | {f.departure_time:<10} | {format_price(f.final_price or f.price):<12}")
                
        elif args.mode == "bus":
            results = await client.search_buses(args.origin, args.destination, args.date)
            if not results:
                print("No buses found.")
                return
            print(f"\n{'Operator':<25} | {'Type':<15} | {'Price':<12} | {'Rating'}")
            print("-" * 65)
            for b in results:
                price = getattr(b, "final_price", None) or getattr(b, "min_price", 0)
                operator_name = getattr(b.operator, "name", "N/A")
                print(f"{operator_name[:24]:<25} | {b.bus_type[:14]:<15} | {format_price(price):<12} | {b.rating or 'N/A'}")
        
        else: # unified search
            res = await client.search_all(args.origin, args.destination, args.date)
            summary = res.summary()
            print("\n" + "="*40)
            print(f"SEARCH SUMMARY: {summary['from']} -> {summary['to']} ({summary['date']})")
            print("="*40)
            print(f"Flights: {summary['flight_count']} found (Lowest: {format_price(summary['cheapest_flight'])})")
            print(f"Trains:  {summary['train_count']} found (Lowest: {format_price(summary['cheapest_train'])})")
            print(f"Buses:   {summary['bus_count']} found (Lowest: {format_price(summary['cheapest_bus'])})")
            print("-" * 40)
            if summary.get("top_flight_info"): print(f"Top Flight: {summary['top_flight_info']}")
            if summary.get("top_train_info"): print(f"Top Train:  {summary['top_train_info']}")
            if summary.get("top_bus_info"): print(f"Top Bus:    {summary['top_bus_info']}")

async def run_list(args):
    """Execution logic for the 'list' subcommand."""
    client = TravelClient() # No need to init fully for DB lookup
    if args.type == "provinces":
        items = client.get_provinces()
        print(f"\n{'ID':<4} | {'Name':<25} | {'Code'}")
        print("-" * 40)
        for item in items:
            print(f"{item['id']:<4} | {item['name']:<25} | {item.get('code', 'N/A')}")
    elif args.type == "airports":
        items = client.get_airports()
        print(f"\n{'IATA':<5} | {'City':<20} | {'Name'}")
        print("-" * 50)
        for item in items:
            print(f"{item.get('iata', 'N/A'):<5} | {item.get('city', 'N/A'):<20} | {item['name']}")
    elif args.type == "stations":
        items = client.get_train_stations()
        print(f"\n{'Code':<5} | {'Name'}")
        print("-" * 30)
        for item in items:
            print(f"{item['code']:<5} | {item['name']}")

def main():
    # Pre-process sys.argv to be more forgiving with flags like --list or --search
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            sys.argv[1] = "list"
        elif sys.argv[1] == "--search":
            sys.argv[1] = "search"

    try:
        version = importlib.metadata.version("travel-sdk")
    except importlib.metadata.PackageNotFoundError:
        version = "0.0.0-dev"

    parser = argparse.ArgumentParser(
        prog="travel-sdk",
        description="Vietnam Transportation SDK CLI - Search for trains, buses, and flights."
    )
    parser.add_argument("--version", action="version", version=f"travel-sdk {version}")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for tickets (e.g. search --from Hanoi --to Saigon)")
    search_parser.add_argument("--from", dest="origin", required=True, help="Origin location (name or code)")
    search_parser.add_argument("--to", dest="destination", required=True, help="Destination location (name or code)")
    search_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Departure date (YYYY-MM-DD)")
    search_parser.add_argument("--mode", choices=["all", "train", "bus", "flight"], default="all", help="Transportation mode")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List locations (provinces, airports, stations)")
    list_parser.add_argument("type", choices=["provinces", "airports", "stations"], nargs="?", default="provinces", help="Type of locations to list (default: provinces)")
    
    # Handle cases where user might use flags for subcommands or need help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    
    if args.command == "search":
        asyncio.run(run_search(args))
    elif args.command == "list":
        asyncio.run(run_list(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
