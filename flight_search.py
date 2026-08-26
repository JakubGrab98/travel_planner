"""Module responsible for communication with the flight API"""
import logging
import requests

import config
from flight_data import FlightData

logger = logging.getLogger(__name__)


class FlightSearch():
    """Retrieve information about the flight based on user parameters.
    Provide data like deistnation airport code or the cheapiest flight details"""

    API_KEY = config.KIWI_API_KEY
    LOCATION_URL = "https://api.tequila.kiwi.com/locations/query"
    SEARCH_URL = "https://api.tequila.kiwi.com/v2/search?"

    HEADERS = {
        "apikey": API_KEY,
    }
    
    def __init__(self) -> None:
        self.flight_details = {}

    def get_airport_code(self, city_name:str) -> str | None:
        """Retrieve airport code based on the choosed city by the user

        Args:
            city_name (str): Name of the city which airport code should be assigned.

        Returns:
            str: Airport IATA code.
        """
        try:
            response = requests.get(
                url=self.LOCATION_URL,
                headers=self.HEADERS,
                params={"term": city_name,
                        "location_types": "airport",
                    }
            )
            data = response.json()
            locations = data["locations"]
            # Kiwi's search is a loose substring match against airport/city names -- e.g.
            # a search for "Rome" can return San Salvador first, because its airport is
            # named after "Monsenor Oscar Arnulfo Romero" (containing "Rome" as a
            # substring). Prefer a location whose city name actually matches the query
            # before falling back to the raw first result.
            for location in locations:
                city = location.get("city") or {}
                if isinstance(city, dict) and city.get("name", "").lower() == city_name.lower():
                    return location["id"]
            return locations[0]["id"]
        except IndexError as e:
            logger.error("Airport code not found.")
            e.add_note("No airport in this destination")
            return None

    def get_flight_data(self, params: dict) -> None | FlightData:
        """Search flight detail based on user parameters

        Args:
            params (dict): Flight parameters for retrieving data from KIWI api.

        Returns:
            FlightData | None: Return flight data if there is flight with provided params.
        """
        response = requests.get(self.SEARCH_URL, headers=self.HEADERS, params=params)

        try:
            data = response.json()["data"][0]
            logger.info("Flight data was retrieved!")
            
        except IndexError as e:
            logger.error(e.add_note("No flight available with such parameters"))
            return None
            
        flight_data = FlightData(
            price=data["price"],
            airlines = data["airlines"][0],
            origin_city=data["route"][0]["cityFrom"],
            origin_airport=data["route"][0]["flyFrom"],
            destination_city=data["route"][0]["cityTo"],
            destination_airport=data["route"][0]["flyTo"],
            departure_date=data["route"][0]["local_departure"].split("T")[0],
            departure_time=data["route"][0]["local_departure"].split("T")[1][0:5],
            return_date=data["route"][1]["local_departure"].split("T")[0],
            return_time=data["route"][1]["local_departure"].split("T")[1][0:5],
        )
        return flight_data
