"""
TravelSDK: A Unified Interface for Vietnam's Transportation APIs.

TravelSDK provides programmatic access to real-time travel data, specifically optimized 
for AI Agents and RAG (Retrieval-Augmented Generation) pipelines. 

Key Features:
- Flights: Live search across major carriers (Vietnam Airlines, VietJet, Bamboo, etc.) 
  with detailed baggage, meal, and aircraft info.
- Trains: Full VNR integration with per-car seat availability and car-type amenities.
- Buses: Search results from hundreds of operators with ratings, reviews, and GPS coordinates.
- Combined Search: Parallel querying across all modes with automatic cheapest-filtering.

The SDK models the complex data into clean, Pydantic-validated structures suitable 
for direct consumption by Large Language Models.
"""

from travel.client import TravelClient
from travel.models import (
    TrainTicket,
    BusTicket,
    FlightTicket,
    SearchResult,
    TicketType,
)

__version__ = "0.1.0"
__all__ = [
    "TravelClient",
    "TrainTicket",
    "BusTicket",
    "FlightTicket",
    "SearchResult",
    "TicketType",
]
