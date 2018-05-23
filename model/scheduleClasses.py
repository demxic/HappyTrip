from datetime import datetime, timedelta

import psycopg2

from data.database import CursorFromConnectionPool
from model.timeClasses import Duration


class Carrier(object):

    def __init__(self, carrier_code: str = 'AM'):
        self.carrier_code = carrier_code


class Equipment(object):

    def __init__(self, airplane_code: str = None, max_crew_members: int = None):
        self.airplane_code = airplane_code
        self.max_crew_members = max_crew_members

    def __str__(self):
        if not self.airplane_code:
            eq_string = 3 * ' '
        else:
            eq_string = self.airplane_code
        return eq_string


class Airport(object):

    def __init__(self, iata_code: str, timezone: str = None, viaticum: str = None):
        """
        Represents an airport as a 3 letter code
        """
        self.iata_code = iata_code
        self.timezone = timezone
        self.viaticum = viaticum

    def save_to_db(self):
        with CursorFromConnectionPool() as cursor:
            continent, tz_city = self.timezone.split('/')
            try:
                cursor.execute('INSERT INTO airports (iata_code, continent, tz_city, viaticum_zone) '
                               'VALUES (%s, %s, %s, %s)',
                               (self.iata_code, continent, tz_city, self.viaticum))
            except psycopg2.IntegrityError:
                print("Already stored")

    @classmethod
    def load_from_db_by_iata_code(cls, iata_code):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM airports WHERE iata_code=%s', (iata_code,))
            airport_data = cursor.fetchone()
            timezone = airport_data[1]+'/'+airport_data[2]
            if airport_data:
                return cls(iata_code=airport_data[0], timezone=timezone, viaticum=airport_data[3])
            # Note that you do not need this because any method without a return clause, returns None as default
            # else:
            #     return None

    def __str__(self):
        return "{}".format(self.iata_code)


class CrewMember(object):
    """Defines a CrewMember"""

    def __init__(self, crew_member_id: int = None, name: str = None, pos: str = None, group: str = None,
                 base: Airport = None, seniority: int = None, crewType: str = None):
        self.id = crew_member_id
        self.name = name
        self.pos = pos
        self.group = group
        self.base = base
        self.seniority = seniority
        self.salary = 0
        self.crewType = crewType
        self.line = None

    def __str__(self):
        return "{0:3s} {1:6s}-{2:12s}".format(self.pos, self.id, self.name)


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
        """Enter beginning and ending datetimes"""
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

    @property
    def duration(self):
        return Duration.from_timedelta(self.end - self.begin)

    def __str__(self):
        template = "{0.name} {0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)


class GroundDuty(Marker):
    """
    Represents  training, reserve or special assignments.
    Ground duties do account for some credits
    """

    def __init__(self, name: str, scheduled_itinerary: Itinerary = None, actual_itinerary: Itinerary = None,
                 origin: Airport = None, destination: Airport = None, equipment: Equipment = None):
        super().__init__(name, scheduled_itinerary, actual_itinerary)
        self.equipment = equipment
        self.destination = destination
        self.origin = origin

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

        template = """
        {0.begin:%d%b} {rpt:4s} {0.name:<6s} {0.origin} {0.begin:%H%M} {0.destination} {0.end:%H%M} {rls:4s} {block}       {turn:4s}       {0.equipment}"""
        self.compute_credits()
        block = self._credits['block']
        return template.format(self, rpt=rpt, rls=rls, turn=turn, block=block)


class Flight(GroundDuty):

    def __init__(self, name: str = None, origin: Airport = None, destination: Airport = None,
                 scheduled_itinerary: Itinerary = None, actual_itinerary: Itinerary = None,
                 equipment: Equipment = None, carrier: Carrier = Carrier):
        """
        Holds those necessary fields to represent a Flight Itinerary
        """
        super().__init__(name=name, origin=origin, destination=destination,
                         scheduled_itinerary=scheduled_itinerary, actual_itinerary=actual_itinerary)
        self.equipment = equipment
        self.carrier = carrier
        self.is_flight = True

    @property
    def report(self):
        """Flight's report time"""
        return super().report - timedelta(hours=1)

    @property
    def release(self):
        """Flights's release time """
        return super().release + timedelta(minutes=30)

    def compute_credits(self, creditator=None):
        if self.name.isdigit():
            block = self.duration
            dh = Duration(0)
        else:
            dh = self.duration
            block = Duration(0)
        self._credits = {'block': block, 'dh': dh}

    # def save_to_db(self):
    #     with connect() as connection:
    #         with connection.cursor() as cursor:
    #             # WE NEED THE route id
    #             cursor.execute(sql_config.retrieve_route_id,
    #                            (self.carrier, self.name[-4:], self.origin, self.destination))
    #             try:
    #                 route_id = cursor.fetchone()[0]
    #             except TypeError:
    #                 # Route needs to be created
    #                 # print("Warning!!!!!!!      New route found: ")
    #                 # print('{} {} {} {}'.format(self.carrier, self.name, self.origin, self.destination))
    #                 cursor.execute(sql_config.create_route, (self.carrier,
    #                                                          self.name[-4:],
    #                                                          self.origin,
    #                                                          self.destination))
    #                 route_id = cursor.fetchone()
    #             # LET'S STORE THE FLIGHT
    #             scheduled_departure_date = self.published_itinerary.begin.date()
    #             scheduled_departure_time = self.published_itinerary.begin.time()
    #             scheduled_block = self.duration.as_timedelta()
    #             scheduled_equipment = self.equipment
    #             cursor.execute(sql_config.select_or_insert_flight,
    #                            (route_id, scheduled_departure_date, scheduled_departure_time,
    #                             scheduled_block, scheduled_equipment,
    #                             route_id, scheduled_departure_date))
    #             self.id = cursor.fetchone()[0]

    # @classmethod
    # def load_from_db_by_fields(cls, name, origin, destination, scheduled_departure_date, carrier_code='AM'):
    #     with connect() as connection:
    #         with connection.cursor() as cursor:
    #             cursor.execute(sql_config.load_flight_by_fields,
    #                            (carrier_code, name[-4:], origin, destination, scheduled_departure_date))
    #             flight_data = cursor.fetchone()
    #             if flight_data:
    #                 carrier_code = flight_data[0]
    #                 flight_number = flight_data[1]
    #                 departure_airport = flight_data[2]
    #                 arrival_airport = flight_data[3]
    #                 scheduled_departure_date = flight_data[4]
    #                 scheduled_departure_time = flight_data[5]
    #                 scheduled_departure = datetime.combine(scheduled_departure_date, scheduled_departure_time)
    #                 scheduled_block = flight_data[6]
    #                 scheduled_arrival = scheduled_departure + scheduled_block
    #                 scheduled_equipment = flight_data[7]
    #                 actual_departure_date = flight_data[8]
    #                 actual_departure_time = flight_data[9]
    #                 # actual_departure = datetime.combine(actual_departure_date, actual_departure_time)
    #                 actual_block = flight_data[10]
    #                 # actual_arrival = actual_departure + actual_block
    #                 actual_equipment = flight_data[11]
    #                 published_itinerary = Itinerary(scheduled_departure, scheduled_arrival)
    #                 # actual_itinerary = Itinerary(actual_departure, actual_arrival)
    #                 actual_itinerary = None
    #                 # print(flight_number, origin, destination, published_itinerary, actual_itinerary,
    #                 #       scheduled_equipment, carrier_code)
    #                 return cls(name=flight_number,
    #                            origin=departure_airport,
    #                            destination=arrival_airport,
    #                            published_itinerary=published_itinerary,
    #                            actual_itinerary=actual_itinerary,
    #                            equipment=scheduled_equipment,
    #                            carrier=carrier_code)

    def __str__(self):
        template = """
        {0.begin:%d%b} {0.name:>6s} {0.origin} {0.begin:%H%M} {0.destination} {0.end:%H%M}\
        {0.duration:2}        {0.equipment}
        """
        return template.format(self)


class DutyDay(object):
    """
    A DutyDay is a collection of Events, it is not a representation of a regular calendar day,
    but rather the collection of Events to be served within a given Duty.
    """

    def __init__(self):
        self.events = []
        self._credits = {}
        self._report = None

    @property
    def begin(self):
        return self.events[0].begin

    @property
    def end(self):
        return self.events[-1].end

    @property
    def report(self):
        return self._report if self._report else self.events[0].report

    @property
    def release(self):
        return self.events[-1].release

    @property
    def delay(self):
        delay = Duration.from_timedelta(self.begin - self.report) - Duration(60)
        return delay

    @property
    def duration(self):
        """How long is the DutyDay"""
        return Duration.from_timedelta(self.release - self.report)

    @property
    def turns(self):
        return [Duration.from_timedelta(j.begin - i.end) for i, j in zip(self.events[:-1], self.events[1:])]

    @property
    def origin(self):
        return self.events[0].origin

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.report, self.release]"""
        delta = self.release.date() - self.report.date()
        all_dates = [self.report.date() + timedelta(days=i) for i in range(delta.days + 1)]
        return all_dates

    def compute_credits(self, creditator=None):
        """Cares only for block, dh, total and daily"""
        # TODO : Take into consideration whenever there is a change in month
        if creditator:
            creditator.credits_from_duty_day(self)
        else:
            self._credits['block'] = Duration(0)
            self._credits['dh'] = Duration(0)
            for event in self.events:
                event.compute_credits(creditator)
                self._credits['block'] += event._credits['block']
                self._credits['dh'] += event._credits['dh']

            self._credits.update({'daily': self.duration,
                                  'total': self._credits['block'] + self._credits['dh']})
        return [self._credits]

    def append(self, current_duty):
        """Add a duty, one by one  to this DutyDay"""
        self.events.append(current_duty)

    def merge(self, other):
        if self.report <= other.report:
            all_events = self.events + other.events
        else:
            all_events = other.events + self.events
        self.events = []
        for event in all_events:
            self.events.append(event)

    def how_many_sundays(self):
        sundays = []
        if self.report.isoweekday() == '7':
            sundays.append(self.report.date())
        if self.release.isoweekday() == '7':
            sundays.append(self.release.date())
        return len(sundays)

    # def save_to_db(self, cursor, containing_trip):
    #     report = self.report.time()
    #     release = None
    #     for flight in self.events:
    #         flight.save_to_db()
    #         # print("Flight_id = ", flight._id)
    #         cursor.execute(sql_config.select_or_insert_flight_to_trip,
    #                        (flight.id, containing_trip.number, containing_trip.dated,
    #                         report, release, not flight.name.isdigit(), flight.id,
    #                         containing_trip.number, containing_trip.dated))
    #         report = None
    #     flight_to_trip_id = cursor.fetchone()[0]
    #     # print("flight_to_trip_id : ", flight_to_trip_id)
    #     release = self.release.time()
    #     cursor.execute(sql_config.update_flight_to_trip_release, (release, flight_to_trip_id))

    def __str__(self):
        """The string representation of the current DutyDay"""
        rpt = '{:%H%M}'.format(self.report)
        rls = '    '
        body = ''
        if len(self.events) > 1:
            for event, turn in zip(self.events, self.turns):
                turn = format(turn, '0')
                body = body + event.as_robust_string(rpt, rls, turn)
                rpt = 4 * ''
            rls = '{:%H%M}'.format(self.release)
            body = body + self.events[-1].as_robust_string(rls=rls)
        else:
            rls = '{:%H%M}'.format(self.release)
            body = self.events[-1].as_robust_string(rpt, rls, 4 * '')

        return body


class Trip(object):
    """
        A trip_match is a collection of DutyDays
        It should be started by passing in a Trip number
    """

    def __init__(self, number: str, dated: datetime.date) -> None:
        self.number = number
        self.duty_days = []
        self.dated = dated
        self._credits = {}

    @property
    def report(self):
        return self.duty_days[0].report

    @property
    def release(self):
        return self.duty_days[-1].release

    @property
    def rests(self):
        """Returns a list of all calculated rests between each duty_day"""
        return [Duration.from_timedelta(j.report - i.release) for i, j in zip(self.duty_days[:-1], self.duty_days[1:])]

    @property
    def layovers(self):
        """Returns a list of all layover stations """
        return [duty_day.events[-1].destination for duty_day in self.duty_days]

    @property
    def duration(self):
        "Returns total time away from base or TAFB"
        return Duration.from_timedelta(self.release - self.report)

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.report, self.release]"""
        delta = self.release.date() - self.report.date()
        all_dates = [self.report.date() + timedelta(days=i) for i in range(delta.days + 1)]
        return all_dates

    def compute_credits(self, creditator=None):

        if creditator:
            return creditator.credits_from_trip(self)
        else:
            self._credits['block'] = Duration(0)
            self._credits['dh'] = Duration(0)
            self._credits['daily'] = Duration(0)
            for duty_day in self.duty_days:
                duty_day.compute_credits(creditator)
                self._credits['block'] += duty_day._credits['block']
                self._credits['dh'] += duty_day._credits['dh']
                self._credits['daily'] += duty_day._credits['daily']
            self._credits.update({'total': self._credits['block'] + self._credits['dh'],
                                  'tafb': self.duration})

    def append(self, duty_day):
        """Simply append a duty_day"""
        self.duty_days.append(duty_day)

    def pop(self, index=-1):
        return self.duty_days.pop(index)

    def how_many_sundays(self):
        sundays = filter(lambda date: date.isoweekday() == 7, self.get_elapsed_dates())
        return len(list(sundays))

    # def save_to_db(self):
    #     # TODO : Guardar report en el 1er vuelo, y rls en el último del duty_day
    #     with connect() as connection:
    #         with connection.cursor() as cursor:
    #             cursor.execute(sql_config.select_or_insert_trip,
    #                            (self.number, self.dated,
    #                             self.number, self.dated))
    #             self.id = cursor.fetchone()
    #             for duty_day in self.duty_days:
    #                 duty_day.save_to_db(cursor, self)

    def __delitem__(self, key):
        del self.duty_days[key]

    def __getitem__(self, key):
        try:
            item = self.duty_days[key]
        except:
            item = None
        return item

    def __setitem__(self, key, value):
        self.duty_days[key] = value

    def __str__(self):
        self.compute_credits()
        header_template = """
        # {0.number}                                                  CHECK IN AT {0.report:%H:%M}
        {0.report:%d%b%Y}
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN        EQ"""

        body_template = """{duty_day}
                     {destination} {rest}                   {block:0}BL {dh:0}CRD {total:0}TL {daily:0}DY"""

        footer_template = """

          TOTALS     {total:2}TL     {block:2}BL     {dh:2}CR           {tafb:2}TAFB"""

        header = header_template.format(self)
        body = ''

        for duty_day, rest in zip(self.duty_days, self.rests):
            rest = repr(rest)
            body = body + body_template.format(duty_day=duty_day,
                                               destination=duty_day.events[-1].destination,
                                               rest=rest,
                                               **duty_day._credits)
        else:
            duty_day = self.duty_days[-1]
            body = body + body_template.format(duty_day=duty_day,
                                               destination='    ',
                                               rest='    ',
                                               **duty_day._credits)

        footer = footer_template.format(**self._credits)
        return header + body + footer


class Line(object):
    """ Represents an ordered sequence of events for a given month"""

    def __init__(self, month, year, crew_member=None):
        self.duties = []
        self.month = month
        self.year = year
        self.crewMember = crew_member
        self._credits = {}

    def append(self, duty):
        self.duties.append(duty)

    def compute_credits(self, creditator=None):
        self._credits['block'] = Duration(0)
        self._credits['dh'] = Duration(0)
        self._credits['daily'] = Duration(0)
        for duty in self.duties:
            try:
                cr = duty.compute_credits()
                self._credits['block'] += duty._credits['block']
                self._credits['dh'] += duty._credits['dh']
                self._credits['daily'] += duty._credits['daily']
            except AttributeError:
                "Object has no compute_credits() method"
                pass

        if creditator:
            credits_list = creditator.credits_from_line(self)

        return credits_list

    def return_duty(self, dutyId):
        """Return the corresponding duty for the given dutyId"""
        return (duty for duty in self.duties if duty.id == dutyId)

    def __delitem__(self, key):
        del self.duties[key]

    def __getitem__(self, key):
        try:
            item = self.duties[key]
        except:
            item = None
        return item

    def __setitem__(self, key, value):
        self.duties[key] = value

    def __iter__(self):
        return iter(self.duties)

    def return_duty_days(self):
        """Turn all dutydays to a list called dd """
        dd = []
        for element in self.duties:
            if isinstance(element, Trip):
                dd.extend(element.duty_days)
            elif isinstance(element, DutyDay):
                dd.append(element)
        return dd

    def __str__(self):
        return "\n".join(str(d) for d in self.duties)
