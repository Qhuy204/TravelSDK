from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field
from .base import TicketType, Provider

class FlightTicket(BaseModel):
    """Normalized flight ticket."""
    type: TicketType = TicketType.FLIGHT
    id_index: str                              # Raw idIndex from API
    airline_code: str                          # e.g. "9G", "VJ", "VN"
    flight_number: str                         # e.g. "9G809"
    cabin: str = "Economy"                     # Economy, Business

    from_iata: str                             # e.g. "HAN"
    to_iata: str                               # e.g. "SGN"
    from_name: str = ""
    to_name: str = ""

    departure_date: str                        # "YYYY-MM-DD"
    departure_time: str                        # "HH:MM"
    arrival_time: str = ""

    duration_minutes: int = 0

    # Price
    price: int = 0                             # VND (before tax)
    final_price: int = 0                       # VND (total)

    # Airline name
    airline_name: str = ""

    # New detailed information fields
    airplane_name: str = ""
    is_non_stop: bool = True
    description: str = ""
    utilities: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    promotions: list[str] = Field(default_factory=list)
    baggage_info: str = ""

    raw: Optional[Any] = Field(default=None, exclude=True)

    @classmethod
    def from_id_index(cls, id_index: str, **kwargs) -> "FlightTicket":
        """
        Parse FlightTicket from provider idIndex format.
        """
        parts = id_index.split("|")
        if len(parts) >= 8:
            airline = parts[0]
            flight_num = parts[2]
            dep_date = parts[4]
            dep_time = parts[5]
            cabin = parts[8] if len(parts) > 8 else "Economy"

            return cls(
                id_index=id_index,
                airline_code=airline,
                flight_number=flight_num,
                cabin=cabin,
                departure_date=dep_date,
                departure_time=dep_time,
                **kwargs,
            )
        return cls(id_index=id_index, airline_code="", flight_number="", **kwargs)
