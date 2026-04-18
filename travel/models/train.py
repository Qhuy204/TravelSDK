from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field
from .base import TicketType, Provider, SeatOption

class CarInfo(BaseModel):
    """Train car info with available seats."""
    car_id: int
    car_number: str                            # e.g. "1", "2A"
    car_type: str                              # e.g. "Ngồi mềm điều hòa"
    group_code: str                            # NGM, NAC, NAM
    total_available: int
    seat_options: list[SeatOption] = []
    min_price: int = 0                         # VND

class TrainTicket(BaseModel):
    """Normalized train ticket."""
    type: TicketType = TicketType.TRAIN
    id_index: str                              # Raw idIndex from API
    session_id: str = ""
    train_number: str                          # e.g. "SE9"
    operator: Provider

    from_code: str                             # Station code e.g. "HNO"
    to_code: str                               # Station code e.g. "SGO"
    from_name: str = ""
    to_name: str = ""

    departure_date: str                        # "YYYY-MM-DD"
    departure_time: str                        # "HH:MM"
    arrival_date: str = ""
    arrival_time: str = ""

    duration_minutes: int = 0
    distance_km: int = 0
    seat_available: int = 0

    # Price info
    min_price: int = 0                         # VND (cheapest seat)
    cars: list[CarInfo] = []                   # Detailed per-car info

    # New detailed information fields
    description: str = ""
    utilities: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    promotions: list[str] = Field(default_factory=list)
    baggage_info: str = ""
    
    # Train specific
    seat_types: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)

    # Raw API data
    raw: Optional[Any] = Field(default=None, exclude=True)

    @property
    def duration_str(self) -> str:
        h, m = divmod(self.duration_minutes, 60)
        return f"{h}h{m:02d}m"
