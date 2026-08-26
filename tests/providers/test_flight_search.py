"""Tests for flight_search.py: airport-code resolution and flight-data lookup."""
from providers.flight_search import FlightSearch


def _fake_response(mocker, json_data):
    return mocker.Mock(json=mocker.Mock(return_value=json_data))


def test_get_airport_code_prefers_matching_city_name_over_substring_match(mocker):
    # Regression test: Kiwi's location search is a loose substring match, so a query for
    # "Rome" can return San Salvador first (its airport is named after "...Romero",
    # containing "Rome"). The real Rome airports appear later in the list.
    mocker.patch(
        "providers.flight_search.requests.get",
        return_value=_fake_response(mocker, {"locations": [
            {"id": "SAL", "name": "Monsenor Oscar Arnulfo Romero International", "city": {"name": "San Salvador"}},
            {"id": "FCO", "name": "Leonardo da Vinci-Fiumicino Airport", "city": {"name": "Rome"}},
            {"id": "CIA", "name": "Ciampino-G. B. Pastine International", "city": {"name": "Rome"}},
        ]}),
    )

    fs = FlightSearch()
    assert fs.get_airport_code("Rome") == "FCO"


def test_get_airport_code_falls_back_to_first_result_when_no_city_matches(mocker):
    mocker.patch(
        "providers.flight_search.requests.get",
        return_value=_fake_response(mocker, {"locations": [
            {"id": "XYZ", "name": "Some Airport", "city": {"name": "Somewhere Else"}},
        ]}),
    )

    fs = FlightSearch()
    assert fs.get_airport_code("Somewhere") == "XYZ"


def test_get_airport_code_returns_none_when_no_locations(mocker):
    mocker.patch(
        "providers.flight_search.requests.get",
        return_value=_fake_response(mocker, {"locations": []}),
    )

    fs = FlightSearch()
    assert fs.get_airport_code("Nowhereville") is None


def test_get_flight_data_returns_none_when_no_results(mocker):
    mocker.patch(
        "providers.flight_search.requests.get",
        return_value=_fake_response(mocker, {"data": []}),
    )

    fs = FlightSearch()
    assert fs.get_flight_data({"fly_from": "WAW", "fly_to": "FCO"}) is None


def test_get_flight_data_returns_flight_data_on_success(mocker):
    mocker.patch(
        "providers.flight_search.requests.get",
        return_value=_fake_response(mocker, {"data": [{
            "price": 199,
            "airlines": ["LOT"],
            "route": [
                {"cityFrom": "Warsaw", "flyFrom": "WAW", "cityTo": "Rome", "flyTo": "FCO",
                 "local_departure": "2026-10-01T08:00:00.000Z"},
                {"local_departure": "2026-10-05T18:00:00.000Z"},
            ],
        }]}),
    )

    fs = FlightSearch()
    result = fs.get_flight_data({"fly_from": "WAW", "fly_to": "FCO"})
    assert result.price == 199
    assert result.origin_city == "Warsaw"
    assert result.destination_airport == "FCO"
    assert result.departure_date == "2026-10-01"
    assert result.return_time == "18:00"
