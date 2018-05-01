class Viaticum(object):
    pass


class Airport(object):

    def __init__(self, iata_code: str, timezone: str = None, viaticum: Viaticum = None) -> None:
        """
        Represents an airport as a 3 letter code
        """
        self.iata_code = iata_code
        self.timezone = timezone
        self.viaticum = viaticum

    def __str__(self):
        return "{}".format(self.iata_code)


class Route(object):
    """For a given airline, represents a flight number as well as origin and destination airports"""

    def __init__(self, flight_number: str, departure_airport: Airport, arrival_airport: Airport,
                 route_id: int = None, carrier_code: str = 'AM', ) -> None:
        self.flight_number = flight_number
        self.departure_airport = departure_airport
        self.arrival_airport = arrival_airport
        self._id = route_id
        self.carrier_code = carrier_code

    def __str__(self):
        return "{} {} {} {}".format(self.carrier_code, self.flight_number,
                                    self.departure_airport, self.arrival_airport)
