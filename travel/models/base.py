from __future__ import annotations
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel

class TicketType(str, Enum):
    TRAIN = "train"
    BUS = "bus"
    FLIGHT = "flight"

class SeatClass(str, Enum):
    """Common seat class categories."""
    SOFT_SEAT = "soft_seat"           # Ngồi mềm
    HARD_SEAT = "hard_seat"           # Ngồi cứng
    SLEEPER_6 = "sleeper_6"           # Nằm khoang 6
    SLEEPER_4 = "sleeper_4"           # Nằm khoang 4
    VIP = "vip"
    ECONOMY = "economy"
    BUSINESS = "business"
    PREMIUM_ECONOMY = "premium_economy"
    UNKNOWN = "unknown"

class Provider(BaseModel):
    """Transport operator info."""
    code: str = ""
    name: str = ""

class SeatOption(BaseModel):
    """A seat type with price."""
    code: str                                  # Internal code
    label: str                                 # Human readable
    seat_class: SeatClass = SeatClass.UNKNOWN
    price: int                                 # VND
    markup_price: Optional[int] = None        # VND (with markup)
    available: int = 0                         # Number of seats

class PointInfo(BaseModel):
    """Pickup or dropoff point details."""
    name: str = ""
    address: str = ""
    time_offset_minutes: int = 0
    lat: float = 0.0
    lon: float = 0.0

class TokenResponse(BaseModel):
    token_type: str
    access_token: str
    refresh_token: str
    expires_in: int

    @property
    def bearer(self) -> str:
        return f"bearer {self.access_token}"
