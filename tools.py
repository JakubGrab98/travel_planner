"""Claude tool schemas and dispatch for flight/hotel function-calling."""
import logging
from datetime import datetime

from flight_search import FlightSearch
from hotel_search import HotelSearch
from utils import DATE_FORMAT

logger = logging.getLogger(__name__)

FLIGHT_TOOL = {
    "name": "search_flights",
    "description": (
        "Search for the cheapest available flight between two cities on given dates. "
        "Only call this when the traveler has supplied both a departure city and a "
        "destination city plus concrete travel dates."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "departure_city": {"type": "string", "description": "City the traveler departs from."},
            "destination_city": {"type": "string", "description": "City the traveler is flying to."},
            "date_from": {"type": "string", "description": "Outbound departure date, ISO format YYYY-MM-DD."},
            "date_to": {"type": "string", "description": "Return departure date, ISO format YYYY-MM-DD."},
        },
        "required": ["departure_city", "destination_city", "date_from", "date_to"],
    },
}

HOTEL_TOOL = {
    "name": "search_hotels",
    "description": (
        "Search for an available hotel offer in a destination city for given check-in/"
        "check-out dates. Only call this when the traveler has supplied a destination "
        "city plus concrete travel dates."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "destination_city": {"type": "string", "description": "City to search hotels in."},
            "check_in_date": {"type": "string", "description": "Check-in date, ISO format YYYY-MM-DD."},
            "check_out_date": {"type": "string", "description": "Check-out date, ISO format YYYY-MM-DD."},
        },
        "required": ["destination_city", "check_in_date", "check_out_date"],
    },
}

ALL_TOOLS = [FLIGHT_TOOL, HOTEL_TOOL]


def _execute_flight_search(tool_input: dict) -> dict:
    departure_city = tool_input["departure_city"]
    destination_city = tool_input["destination_city"]

    flight_search = FlightSearch()
    origin_code = flight_search.get_airport_code(departure_city)
    if origin_code is None:
        return {"found": False, "reason": f"No airport found for departure city '{departure_city}'."}

    destination_code = flight_search.get_airport_code(destination_city)
    if destination_code is None:
        return {"found": False, "reason": f"No airport found for destination city '{destination_city}'."}

    try:
        departure = datetime.strptime(tool_input["date_from"], "%Y-%m-%d").date()
        return_date = datetime.strptime(tool_input["date_to"], "%Y-%m-%d").date()
    except ValueError:
        return {"found": False, "reason": "Dates must be in YYYY-MM-DD format."}

    nights = (return_date - departure).days
    if nights <= 0:
        return {"found": False, "reason": "Return date must be after the departure date."}

    # Kiwi's date_from/date_to define a *search window* for the outbound leg, not fixed
    # travel dates -- narrowing both to the same day pins the exact departure date
    # requested. nights_in_dst_from/to (both set to the requested trip length) is what
    # actually determines the return leg's date; dropping them (as a naive date_from=
    # outbound/date_to=return mapping would) either searches the wrong date range or comes
    # back one-way-only, which crashes downstream on the missing return-leg fields.
    kiwi_date = departure.strftime(DATE_FORMAT)
    params = {
        "fly_from": origin_code,
        "fly_to": destination_code,
        "date_from": kiwi_date,
        "date_to": kiwi_date,
        "nights_in_dst_from": nights,
        "nights_in_dst_to": nights,
        "curr": "EUR",
        "max_stopovers": 1,
    }

    try:
        flight_data = flight_search.get_flight_data(params)
    except Exception:  # noqa: BLE001 - never let an upstream failure raise into Claude's loop
        logger.exception("Kiwi flight search request failed.")
        return {"found": False, "reason": "Flight search service is currently unavailable."}

    if flight_data is None:
        return {"found": False, "reason": "No flights found for the given route/dates."}

    return {
        "found": True,
        "price": flight_data.price,
        "airlines": flight_data.airlines,
        "origin_city": flight_data.origin_city,
        "origin_airport": flight_data.origin_airport,
        "destination_city": flight_data.destination_city,
        "destination_airport": flight_data.destination_airport,
        "departure_date": flight_data.departure_date,
        "departure_time": flight_data.departure_time,
        "return_date": flight_data.return_date,
        "return_time": flight_data.return_time,
    }


def _execute_hotel_search(tool_input: dict) -> dict:
    destination_city = tool_input["destination_city"]
    check_in_date = tool_input["check_in_date"]
    check_out_date = tool_input["check_out_date"]

    hotel_search = HotelSearch()

    try:
        city_code = hotel_search.get_city_code(destination_city)
        if city_code is None:
            return {"found": False, "reason": f"No city code found for '{destination_city}'."}

        hotel_ids = hotel_search.get_hotel_ids(city_code)
        if not hotel_ids:
            return {"found": False, "reason": f"No hotels found in '{destination_city}'."}

        hotel_offer = hotel_search.get_hotel_offers(hotel_ids, check_in_date, check_out_date)
    except Exception:  # noqa: BLE001 - never let an upstream failure raise into Claude's loop
        logger.exception("Amadeus hotel search request failed.")
        return {"found": False, "reason": "Hotel search service is currently unavailable."}

    if hotel_offer is None:
        return {"found": False, "reason": "No hotel offers found for the given city/dates."}

    return {
        "found": True,
        "hotel_name": hotel_offer.hotel_name,
        "city": hotel_offer.city,
        "check_in_date": hotel_offer.check_in_date,
        "check_out_date": hotel_offer.check_out_date,
        "price": hotel_offer.price,
        "currency": hotel_offer.currency,
        "room_description": hotel_offer.room_description,
    }


_DISPATCH = {
    "search_flights": _execute_flight_search,
    "search_hotels": _execute_hotel_search,
}


def execute_tool_call(tool_name: str, tool_input: dict) -> dict:
    """Execute a Claude tool call by name, never raising.

    Args:
        tool_name (str): one of ALL_TOOLS' "name" values.
        tool_input (dict): the tool_use block's parsed input.

    Returns:
        dict: a structured, JSON-serializable result. Unknown tool names or unexpected
            errors degrade to a {"found": False, "reason": ...} dict rather than raising --
            this is what fixes the flight-tool bug: the crash was always about an
            unguarded None/exception reaching the caller, and this dispatcher guarantees
            the caller (Claude, via tool_result) always gets a well-formed dict instead.
    """
    handler = _DISPATCH.get(tool_name)
    if handler is None:
        return {"found": False, "reason": f"Unknown tool '{tool_name}'."}

    try:
        return handler(tool_input)
    except Exception:  # noqa: BLE001 - dispatcher must never raise into the caller
        logger.exception("Tool execution crashed for tool=%s input=%s", tool_name, tool_input)
        return {"found": False, "reason": "Tool execution failed unexpectedly."}
