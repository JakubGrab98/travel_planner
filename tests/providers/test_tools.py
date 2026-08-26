"""Tests for tools.py: the dispatcher and both tool execution wrappers."""
from providers.flight_data import FlightData
from providers.hotel_data import HotelOffer
from providers.tools import execute_tool_call


def test_execute_tool_call_unknown_tool_name():
    assert execute_tool_call("search_unicorns", {}) == {
        "found": False, "reason": "Unknown tool 'search_unicorns'."
    }


# --- search_flights ---

def test_search_flights_origin_airport_not_found(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.return_value = None

    result = execute_tool_call("search_flights", {
        "departure_city": "Nowhereville", "destination_city": "Paris",
        "date_from": "2026-09-01", "date_to": "2026-09-05",
    })
    assert result["found"] is False
    assert "Nowhereville" in result["reason"]


def test_search_flights_destination_airport_not_found_never_hits_kiwi_search(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.side_effect = ["WAW", None]

    result = execute_tool_call("search_flights", {
        "departure_city": "Warsaw", "destination_city": "Nowhereville",
        "date_from": "2026-09-01", "date_to": "2026-09-05",
    })
    assert result["found"] is False
    mock_cls.return_value.get_flight_data.assert_not_called()


def test_search_flights_no_results_from_kiwi(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.side_effect = ["WAW", "CDG"]
    mock_cls.return_value.get_flight_data.return_value = None

    result = execute_tool_call("search_flights", {
        "departure_city": "Warsaw", "destination_city": "Paris",
        "date_from": "2026-09-01", "date_to": "2026-09-05",
    })
    assert result == {"found": False, "reason": "No flights found for the given route/dates."}


def test_search_flights_converts_dates_and_computes_nights(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.side_effect = ["WAW", "CDG"]
    mock_cls.return_value.get_flight_data.return_value = None

    execute_tool_call("search_flights", {
        "departure_city": "Warsaw", "destination_city": "Paris",
        "date_from": "2026-09-01", "date_to": "2026-09-05",
    })
    params = mock_cls.return_value.get_flight_data.call_args.args[0]
    assert params["fly_from"] == "WAW"
    assert params["fly_to"] == "CDG"
    # Kiwi's date_from/date_to define a search window for the outbound leg, not fixed
    # travel dates -- both must be pinned to the exact departure date, with the trip
    # length carried via nights_in_dst_from/to instead.
    assert params["date_from"] == "01/09/2026"
    assert params["date_to"] == "01/09/2026"
    assert params["nights_in_dst_from"] == 4
    assert params["nights_in_dst_to"] == 4


def test_search_flights_rejects_return_before_departure(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.side_effect = ["WAW", "CDG"]

    result = execute_tool_call("search_flights", {
        "departure_city": "Warsaw", "destination_city": "Paris",
        "date_from": "2026-09-05", "date_to": "2026-09-01",
    })
    assert result["found"] is False
    mock_cls.return_value.get_flight_data.assert_not_called()


def test_search_flights_success(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.side_effect = ["WAW", "CDG"]
    mock_cls.return_value.get_flight_data.return_value = FlightData(
        price=250, airlines="LOT", origin_city="Warsaw", origin_airport="WAW",
        destination_city="Paris", destination_airport="CDG",
        departure_date="2026-09-01", departure_time="08:00",
        return_date="2026-09-05", return_time="18:00",
    )

    result = execute_tool_call("search_flights", {
        "departure_city": "Warsaw", "destination_city": "Paris",
        "date_from": "2026-09-01", "date_to": "2026-09-05",
    })
    assert result["found"] is True
    assert result["price"] == 250
    assert result["airlines"] == "LOT"


def test_search_flights_upstream_exception_becomes_structured_failure(mocker):
    mock_cls = mocker.patch("providers.tools.FlightSearch")
    mock_cls.return_value.get_airport_code.side_effect = ["WAW", "CDG"]
    mock_cls.return_value.get_flight_data.side_effect = RuntimeError("boom")

    result = execute_tool_call("search_flights", {
        "departure_city": "Warsaw", "destination_city": "Paris",
        "date_from": "2026-09-01", "date_to": "2026-09-05",
    })
    assert result["found"] is False


# --- search_hotels ---

def test_search_hotels_city_not_found(mocker):
    mock_cls = mocker.patch("providers.tools.HotelSearch")
    mock_cls.return_value.get_city_code.return_value = None

    result = execute_tool_call("search_hotels", {
        "destination_city": "Nowhereville", "check_in_date": "2026-09-01", "check_out_date": "2026-09-05",
    })
    assert result["found"] is False


def test_search_hotels_no_hotel_ids(mocker):
    mock_cls = mocker.patch("providers.tools.HotelSearch")
    mock_cls.return_value.get_city_code.return_value = "PAR"
    mock_cls.return_value.get_hotel_ids.return_value = None

    result = execute_tool_call("search_hotels", {
        "destination_city": "Paris", "check_in_date": "2026-09-01", "check_out_date": "2026-09-05",
    })
    assert result["found"] is False


def test_search_hotels_no_offers(mocker):
    mock_cls = mocker.patch("providers.tools.HotelSearch")
    mock_cls.return_value.get_city_code.return_value = "PAR"
    mock_cls.return_value.get_hotel_ids.return_value = ["HT1"]
    mock_cls.return_value.get_hotel_offers.return_value = None

    result = execute_tool_call("search_hotels", {
        "destination_city": "Paris", "check_in_date": "2026-09-01", "check_out_date": "2026-09-05",
    })
    assert result == {"found": False, "reason": "No hotel offers found for the given city/dates."}


def test_search_hotels_success(mocker):
    mock_cls = mocker.patch("providers.tools.HotelSearch")
    mock_cls.return_value.get_city_code.return_value = "PAR"
    mock_cls.return_value.get_hotel_ids.return_value = ["HT1"]
    mock_cls.return_value.get_hotel_offers.return_value = HotelOffer(
        hotel_name="Hotel Test", city="PAR", check_in_date="2026-09-01", check_out_date="2026-09-05",
        price=450.0, currency="EUR", room_description="Double room",
    )

    result = execute_tool_call("search_hotels", {
        "destination_city": "Paris", "check_in_date": "2026-09-01", "check_out_date": "2026-09-05",
    })
    assert result["found"] is True
    assert result["hotel_name"] == "Hotel Test"


def test_search_hotels_upstream_exception_becomes_structured_failure(mocker):
    mock_cls = mocker.patch("providers.tools.HotelSearch")
    mock_cls.return_value.get_city_code.side_effect = RuntimeError("boom")

    result = execute_tool_call("search_hotels", {
        "destination_city": "Paris", "check_in_date": "2026-09-01", "check_out_date": "2026-09-05",
    })
    assert result["found"] is False
