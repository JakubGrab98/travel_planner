"""Module with class for stucturing flight data"""
from dataclasses import dataclass

@dataclass
class FlightData:
    """Class for structuring flight parameters for searching the cheapiest flight"""
    price: float
    origin_city: str
    origin_airport: str
    destination_city: str
    destination_airport: str
    departure_date: str
    departure_time: str
    return_date: str
    return_time: str

    def __str__(self):
        data_summary = f"""
            Flight from: {self.origin_city} ({self.origin_airport}) to: {self.destination_city} ({self.destination_airport})\n,
            deperture: {self.departure_date} | {self.departure_time}\n;
            arrival: {self.return_date} | {self.return_time}\n.
            Price: {self.price} PLN
        """
        return str(data_summary)
    