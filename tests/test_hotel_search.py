"""Tests for hotel_search.py: the 3-step Amadeus flow's success/failure paths."""
from amadeus import ResponseError

from hotel_search import HotelSearch


def _fake_response_error():
    # Bypasses ResponseError.__init__ (which needs a real Response object we don't have
    # in a unit test) while still producing a valid raisable ResponseError instance.
    return ResponseError.__new__(ResponseError)


def _make_hotel_search(mocker):
    mocker.patch("hotel_search.Client")
    return HotelSearch()


def test_get_city_code_returns_iata_code_on_success(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.reference_data.locations.get.return_value = mocker.Mock(data=[{"iataCode": "PAR"}])
    assert hs.get_city_code("Paris") == "PAR"


def test_get_city_code_returns_none_when_no_match(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.reference_data.locations.get.return_value = mocker.Mock(data=[])
    assert hs.get_city_code("Nowhereville") is None


def test_get_city_code_returns_none_on_api_error(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.reference_data.locations.get.side_effect = _fake_response_error()
    assert hs.get_city_code("Paris") is None


def test_get_hotel_ids_returns_list_on_success(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.reference_data.locations.hotels.by_city.get.return_value = mocker.Mock(
        data=[{"hotelId": "HTPAR001"}, {"hotelId": "HTPAR002"}]
    )
    assert hs.get_hotel_ids("PAR") == ["HTPAR001", "HTPAR002"]


def test_get_hotel_ids_returns_none_when_empty(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.reference_data.locations.hotels.by_city.get.return_value = mocker.Mock(data=[])
    assert hs.get_hotel_ids("PAR") is None


def test_get_hotel_ids_returns_none_on_api_error(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.reference_data.locations.hotels.by_city.get.side_effect = _fake_response_error()
    assert hs.get_hotel_ids("PAR") is None


def test_get_hotel_offers_returns_hotel_offer_on_success(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.shopping.hotel_offers_search.get.return_value = mocker.Mock(
        data=[{
            "hotel": {"name": "Hotel Test", "cityCode": "PAR"},
            "offers": [{
                "checkInDate": "2026-09-01",
                "checkOutDate": "2026-09-05",
                "price": {"total": "450.00", "currency": "EUR"},
                "room": {"description": {"text": "Double room"}},
            }],
        }]
    )
    offer = hs.get_hotel_offers(["HTPAR001"], "2026-09-01", "2026-09-05")
    assert offer.hotel_name == "Hotel Test"
    assert offer.price == 450.00


def test_get_hotel_offers_returns_none_when_empty(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.shopping.hotel_offers_search.get.return_value = mocker.Mock(data=[])
    assert hs.get_hotel_offers(["HTPAR001"], "2026-09-01", "2026-09-05") is None


def test_get_hotel_offers_returns_none_on_api_error(mocker):
    hs = _make_hotel_search(mocker)
    hs.client.shopping.hotel_offers_search.get.side_effect = _fake_response_error()
    assert hs.get_hotel_offers(["HTPAR001"], "2026-09-01", "2026-09-05") is None
