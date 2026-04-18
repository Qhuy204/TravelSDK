from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field
from .base import TicketType, Provider, PointInfo

class BusTicket(BaseModel):
    """Normalized bus ticket."""
    type: TicketType = TicketType.BUS
    id_index: str = ""
    session_id: str = ""
    operator: Provider

    from_id: int                               # Bus region ID
    to_id: int
    from_name: str = ""
    to_name: str = ""

    departure_date: str                        # "YYYY-MM-DD"
    departure_time: str                        # "HH:MM"
    arrival_time: str = ""

    duration_minutes: int = 0
    seat_available: int = 0
    bus_type: str = ""                         # Limousine, Giường nằm, etc.

    # Price
    price: int = 0                             # VND
    final_price: int = 0                       # VND (after discount)

    # Locations
    pickup_points: list[PointInfo] = Field(default_factory=list)
    dropoff_points: list[PointInfo] = Field(default_factory=list)

    # New detailed information fields
    description: str = ""
    utilities: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    promotions: list[str] = Field(default_factory=list)
    baggage_info: str = ""
    
    # Rating & Reviews
    rating: float = 0.0
    reviews: int = 0

    raw: Optional[Any] = Field(default=None, exclude=True)
