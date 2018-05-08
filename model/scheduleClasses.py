from datetime import datetime, timedelta

from model.timeClasses import Duration


class Equipment(object):

    def __init__(self, airplane_code: str=None, max_crew_members: int=None):
        self.airplane_code = airplane_code
        self.max_crew_members = max_crew_members

    def __str__(self):
        if self.airplane_code is None:
            eq_string = 3*''
        else:
            eq_string = "{}".format(self.airplane_code)
        return eq_string


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

    # def compute_credits(self, itinerator=None):
    #     return None
    #
    # def overlaps(self, other):
    #     begin_date = self.begin.date()
    #     overlap = max(0, min(self.end, other.end) - max(self.begin, other.begin))
    #     return overlap

    def __str__(self):
        template = "{0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)


class Marker(object):
    """
    Represents  Vacations, GDO's, time-off, etc.
    Markers don't account for duty or block time in a given month
    """

    def __init__(self, name: str, scheduled_itinerary: Itinerary = None, actual_itinerary: Itinerary = None):
        self.name = name
        self.scheduled_itinerary = scheduled_itinerary
        self.actual_itinerary = actual_itinerary
        self.is_flight = False
        self._credits = None

    @property
    def begin(self):
        return self.actual_itinerary.begin if self.actual_itinerary else self.scheduled_itinerary.begin

    @property
    def end(self):
        return self.actual_itinerary.end if self.actual_itinerary else self.scheduled_itinerary.end

    @property
    def report(self):
        return self.begin

    def __str__(self):
        template = "{0.name} {0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)


class GroundDuty(Marker):
    """
    Represents  training, reserve or special assignments.
    """

    def __init__(self, name: str, scheduled_itinerary: Itinerary = None, actual_itinerary: Itinerary = None,
                 origin: Airport = None, destination: Airport = None, equipment: Equipment = None):
        super().__init__(name, scheduled_itinerary, actual_itinerary)
        self.origin = origin
        self.destination = destination
        self.equipment = equipment

    @property
    def report(self):
        return self.scheduled_itinerary.begin if self.scheduled_itinerary else self.actual_itinerary.begin

    @property
    def release(self):
        return self.end

    def compute_credits(self, creditator=None):
        self._credits = {'block': Duration(0), 'dh': Duration(0)}

    def as_robust_string(self, rpt=4 * '', rls=4 * '', turn=4 * ''):
        """Prints a Ground Duty following this heather template
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN       EQ
        05JUN 0900 E6     MEX 0900 MEX 1500 1500 0000

        OR ********************************************************************
        Prints a Flight following this heather template
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN       EQ
        03JUN 1400 0924   MEX 1500 MTY 1640 1720 0140       0000       738


        Following arguments being optional
        rpt : report
        rls : release
        turn: turn around time
        eq : equipment"""

        template = """{0.begin:%d%b} {rpt:4s} {0.name:<6s} {0.origin} {0.begin:%H%M} {0.destination} {0.end:%H%M} {
        rls:4s} {block:0}       {turn:4s}       {eq} """
        eq = str(self.equipment) if self.equipment else 3 * ''
        self.compute_credits()
        block = self._credits['block']
        return template.format(self, rpt=rpt, rls=rls, turn=turn, eq=eq, block=block)
