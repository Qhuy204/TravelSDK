"""
Tests for TravelSDK - location resolver utilities.
"""

import pytest
from travel.locations import (
    resolve_train_station,
    resolve_flight_airport,
    resolve_bus_region,
)


class TestTrainStationResolver:
    def test_resolve_by_code(self):
        result = resolve_train_station("HNO")
        assert result is not None
        assert result["code"] == "HNO"

    def test_resolve_by_key(self):
        result = resolve_train_station("hanoi")
        assert result is not None
        assert result["code"] == "HNO"

    def test_resolve_by_vietnamese_name(self):
        result = resolve_train_station("Hà Nội")
        assert result is not None
        assert result["code"] == "HNO"

    def test_resolve_by_alias(self):
        result = resolve_train_station("hcm")
        assert result is not None
        assert result["code"] == "SGO"

    def test_resolve_saigon(self):
        result = resolve_train_station("Sài Gòn")
        assert result is not None
        assert result["code"] == "SGO"

    def test_resolve_invalid(self):
        result = resolve_train_station("XYZ_INVALID_CITY")
        assert result is None


class TestFlightAirportResolver:
    def test_resolve_by_iata(self):
        result = resolve_flight_airport("HAN")
        assert result is not None
        assert result["iata"] == "HAN"

    def test_resolve_by_city(self):
        result = resolve_flight_airport("Hà Nội")
        assert result is not None
        assert result["iata"] == "HAN"

    def test_resolve_sgn(self):
        result = resolve_flight_airport("SGN")
        assert result is not None
        assert result["iata"] == "SGN"

    def test_resolve_saigon_alias(self):
        result = resolve_flight_airport("tphcm")
        assert result is not None
        assert result["iata"] == "SGN"

    def test_resolve_danang(self):
        result = resolve_flight_airport("Đà Nẵng")
        assert result is not None
        assert result["iata"] == "DAD"

    def test_invalid(self):
        result = resolve_flight_airport("INVALID_PLACE_XYZ")
        assert result is None


class TestBusRegionResolver:
    def test_resolve_hanoi(self):
        result = resolve_bus_region("Hà Nội")
        assert result is not None
        assert result["id"] == 124

    def test_resolve_saigon(self):
        result = resolve_bus_region("Sài Gòn")
        assert result is not None
        assert result["id"] == 1291

    def test_resolve_by_key(self):
        result = resolve_bus_region("hanoi")
        assert result is not None
        assert result["id"] == 124

    def test_resolve_by_alias(self):
        result = resolve_bus_region("hcm")
        assert result is not None
        assert result["id"] == 1291

    def test_invalid(self):
        result = resolve_bus_region("NOWHERE_XYZ")
        assert result is None
