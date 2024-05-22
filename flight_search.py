"""Module responsible for communication with the flight API"""
import logging
import os
import requests
from dotenv import load_dotenv
from flight_data import FlightData

load_dotenv()
logger = logging.getLogger(__name__)


class FlightSearch():
    """Retrieve information about the flight based on user parameters.
    Provide data like deistnation airport code or the cheapiest flight details"""

    API_KEY = os.getenv("KIWI_API_KEY")
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
            city_code = data["locations"][0]["id"]
            return city_code
        except IndexError as e:
            logger.error("Airport code not found.")
            e.add_note("No airport in this destination")
            return None

    def get_flight_data(self, params: dict) -> FlightData | None:
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
