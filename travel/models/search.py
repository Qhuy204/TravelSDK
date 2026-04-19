from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel
from .train import TrainTicket
from .bus import BusTicket
from .flight import FlightTicket

class SearchResult(BaseModel):
    """Unified search result containing all ticket types."""
    query_from: str
    query_to: str
    query_date: str
    query_passengers: int = 1

    trains: list[TrainTicket] = []
    buses: list[BusTicket] = []
    flights: list[FlightTicket] = []

    # Metadata
    searched_at: Optional[str] = None

    @property
    def all_tickets(self) -> list[TrainTicket | BusTicket | FlightTicket]:
        """Returns all tickets sorted by price."""
        all_t: list[Any] = []
        all_t.extend(self.trains)
        all_t.extend(self.buses)
        all_t.extend(self.flights)
        
        def _get_price(t) -> int:
            return _get_ticket_price(t)
            
        return sorted(all_t, key=_get_price)

    def sort_tickets(self, tickets: list[Any], by: str = "price", reverse: bool = False) -> list[Any]:
        """Sort tickets by a specific criterion."""
        if by == "price":
            return sorted(tickets, key=_get_ticket_price, reverse=reverse)
        elif by == "time":
            return sorted(tickets, key=lambda t: getattr(t, "departure_time", ""), reverse=reverse)
        elif by in ("airline", "operator"):
            return sorted(tickets, key=lambda t: getattr(t, "airline_name", "") or getattr(getattr(t, "operator", None), "name", ""), reverse=reverse)
        return tickets

    def cheapest(self) -> Optional[TrainTicket | BusTicket | FlightTicket]:
        """Returns the cheapest ticket across all types."""
        tickets = self.all_tickets
        return tickets[0] if tickets else None

    def summary(self) -> dict:
        """Returns a concise summary for LLM consumption."""
        res = {
            "from": self.query_from,
            "to": self.query_to,
            "date": self.query_date,
            "train_count": len(self.trains),
            "bus_count": len(self.buses),
            "flight_count": len(self.flights),
            "cheapest_train": min((t.min_price for t in self.trains), default=None),
            "cheapest_bus": min((t.final_price or t.price for t in self.buses), default=None),
            "cheapest_flight": min((t.final_price or t.price for f in self.flights), default=None),
        }
        if self.trains:
            t = sorted(self.trains, key=_get_ticket_price)[0]
            res["top_train_info"] = f"Tàu {t.train_number} ({t.departure_time}) - {t.min_price}đ"
        if self.buses:
            b = sorted(self.buses, key=_get_ticket_price)[0]
            res["top_bus_info"] = f"Xe {b.operator.name} ({b.departure_time}) - {b.final_price}đ"
        if self.flights:
            f = sorted(self.flights, key=_get_ticket_price)[0]
            res["top_flight_info"] = f"Bay {f.airline_name} ({f.departure_time}) - {f.final_price}đ"
        return res

def _get_ticket_price(ticket: Any) -> int:
    """Universal helper to extract the best price from any ticket type."""
    if hasattr(ticket, "final_price") and getattr(ticket, "final_price"):
        return ticket.final_price
    if hasattr(ticket, "min_price") and getattr(ticket, "min_price"):
        return ticket.min_price
    return getattr(ticket, "price", 0)
