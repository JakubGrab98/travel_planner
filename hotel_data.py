"""Module with class for structuring hotel offer data"""
from dataclasses import dataclass


@dataclass
class HotelOffer:
    """Class for structuring hotel offer data returned by the Amadeus Hotel Search API"""
    hotel_name: str
    city: str
    check_in_date: str
    check_out_date: str
    price: float
    currency: str
    room_description: str

    def __str__(self):
        return f"""
            Hotel: {self.hotel_name} in {self.city}
            Check-in: {self.check_in_date} | Check-out: {self.check_out_date}
            Room: {self.room_description}
            Price: {self.price} {self.currency}
        """
