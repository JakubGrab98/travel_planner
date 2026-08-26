"""Module responsible for communication with the hotel API (Amadeus Hotel Search)"""
import logging

from amadeus import Client, Location, ResponseError

import config
from hotel_data import HotelOffer

logger = logging.getLogger(__name__)


class HotelSearch():
    """Retrieve hotel offers for a city via the Amadeus self-service Hotel Search API.
    Three-step flow: city name -> IATA city code -> hotel IDs in that city -> priced
    hotel offers for those IDs."""

    def __init__(self) -> None:
        self.client = Client(
            client_id=config.AMADEUS_CLIENT_ID,
            client_secret=config.AMADEUS_CLIENT_SECRET,
            hostname="test",
        )

    def get_city_code(self, city_name: str) -> str | None:
        """Resolve a city name to an Amadeus/IATA city code.

        Args:
            city_name (str): Name of the city to resolve.

        Returns:
            str | None: IATA city code, or None if no match / API error.
        """
        try:
            response = self.client.reference_data.locations.get(
                keyword=city_name, subType=Location.CITY
            )
            return response.data[0]["iataCode"]
        except ResponseError as error:
            logger.error("City code lookup failed for %s: %s", city_name, error)
            return None
        except (IndexError, KeyError) as error:
            logger.error("No city code found for %s: %s", city_name, error)
            return None

    def get_hotel_ids(self, city_code: str) -> list[str] | None:
        """Retrieve hotel IDs located in the given city.

        Args:
            city_code (str): IATA city code.

        Returns:
            list[str] | None: list of hotel IDs, or None if none found / API error.
        """
        try:
            response = self.client.reference_data.locations.hotels.by_city.get(
                cityCode=city_code
            )
            hotel_ids = [hotel["hotelId"] for hotel in response.data]
            return hotel_ids or None
        except ResponseError as error:
            logger.error("Hotel ID lookup failed for city %s: %s", city_code, error)
            return None

    def get_hotel_offers(
        self, hotel_ids: list[str], check_in_date: str, check_out_date: str
    ) -> HotelOffer | None:
        """Search for priced hotel offers for the given hotel IDs.

        Args:
            hotel_ids (list[str]): candidate hotel IDs (from get_hotel_ids).
            check_in_date (str): ISO YYYY-MM-DD check-in date.
            check_out_date (str): ISO YYYY-MM-DD check-out date.

        Returns:
            HotelOffer | None: the first available priced offer, or None if there are
                no offers / an API error occurs.
        """
        try:
            response = self.client.shopping.hotel_offers_search.get(
                # Amadeus's self-service test tier caps hotelIds per call; capping here
                # keeps a single tool call within that limit regardless of city size.
                hotelIds=",".join(hotel_ids[:20]),
                checkInDate=check_in_date,
                checkOutDate=check_out_date,
            )
            data = response.data[0]
            offer = data["offers"][0]
            return HotelOffer(
                hotel_name=data["hotel"]["name"],
                city=data["hotel"].get("cityCode", ""),
                check_in_date=offer["checkInDate"],
                check_out_date=offer["checkOutDate"],
                price=float(offer["price"]["total"]),
                currency=offer["price"]["currency"],
                room_description=offer.get("room", {}).get("description", {}).get("text", ""),
            )
        except ResponseError as error:
            logger.error("Hotel offers search failed: %s", error)
            return None
        except (IndexError, KeyError) as error:
            logger.error("No hotel offers available: %s", error)
            return None
