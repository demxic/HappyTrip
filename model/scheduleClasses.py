from datetime import datetime, timedelta

from model.timeClasses import Duration


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


class Itinerary(object):
    """ An Itinerary represents a Duration occurring between a 'begin' and an 'end' datetime. """

    def __init__(self, begin: datetime, end: datetime):
        """
        :Duration duration: Duration
        """
        self.begin = begin
        self.end = end

    @classmethod
    def from_timedelta(cls, begin, a_timedelta):
        """Returns an Itinerary from a given begin datetime and the timedelta duration of it"""
        end = begin + a_timedelta
        return cls(begin, end)

    @property
    def duration(self):
        return Duration.from_timedelta(self.end - self.begin)

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.begin, self.end]"""
        delta = self.end.date() - self.begin.date()
        all_dates = (self.begin.date() + timedelta(days=i) for i in range(delta.days + 1))
        return list(all_dates)

    def compute_credits(self, itinerator=None):
        return None

    def overlaps(self, other):
        begin_date = self.begin.date()
        overlap = max(0, min(self.end, other.end) - max(self.begin, other.begin))
        return overlap

    def __str__(self):
        template = "{0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)
