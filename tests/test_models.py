"""Tests for Pydantic models."""

import pytest
from travel.models import (
    TrainTicket,
    BusTicket,
    FlightTicket,
    SearchResult,
    TicketType,
    Provider,
    SeatClass,
    SeatOption,
    CarInfo,
)


class TestFlightTicketParsing:
    def test_from_id_index(self):
        id_index = "9G|N|9G809|0|2026-04-19|6:30|102188|28284|Economy|100"
        ticket = FlightTicket.from_id_index(
            id_index,
            from_iata="HAN",
            to_iata="SGN",
            price=2452000,
            final_price=2452000,
        )
        assert ticket.airline_code == "9G"
        assert ticket.flight_number == "9G809"
        assert ticket.departure_date == "2026-04-19"
        assert ticket.departure_time == "6:30"
        assert ticket.cabin == "Economy"
        assert ticket.price == 2452000

    def test_type_is_flight(self):
        ticket = FlightTicket(
            id_index="VN|Y|VN123|0|2026-04-19|10:00|102188|28284|Economy|0",
            airline_code="VN",
            flight_number="VN123",
            from_iata="HAN",
            to_iata="SGN",
            departure_date="2026-04-19",
            departure_time="10:00",
        )
        assert ticket.type == TicketType.FLIGHT


class TestTrainTicket:
    def test_duration_str(self):
        ticket = TrainTicket(
            id_index="VNR|SE9|2026-04-20|12:50|HNO|SGO",
            train_number="SE9",
            operator=Provider(code="VNR", name="Vietnam Railways"),
            from_code="HNO",
            to_code="SGO",
            departure_date="2026-04-20",
            departure_time="12:50",
            duration_minutes=2330,
        )
        assert "h" in ticket.duration_str
        assert ticket.type == TicketType.TRAIN


class TestSearchResult:
    def test_summary(self):
        result = SearchResult(
            query_from="Hà Nội",
            query_to="Sài Gòn",
            query_date="2026-04-20",
        )
        s = result.summary()
        assert s["train_count"] == 0
        assert s["bus_count"] == 0
        assert s["flight_count"] == 0

    def test_all_tickets_empty(self):
        result = SearchResult(
            query_from="HAN",
            query_to="SGN",
            query_date="2026-04-20",
        )
        assert result.all_tickets == []
        assert result.cheapest() is None
