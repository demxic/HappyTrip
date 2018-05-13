"""
Created on 29/12/2015

@author: Xico

A bidline reader should return a bidline

"""
from data.regex import crewstats_no_type, crewstats_with_type, rosterDayRE, airItineraryRE, itineraryRE, carryInRE
from model.elements import Dotdict
from model.scheduleClasses import Line, Flight, GroundDuty, DutyDay, Trip, Itinerary, Marker, Airport
from datetime import datetime, timedelta
from data import rules
#TODO : Integrate this into my database
temp_airports_dict = {'MEX': Airport('MEX')}
#TODO : This is a dummy equipment that should work as a singleton

class RosterReader(object):
    def __init__(self, fp=None):
        """
        Receives an fp iterable and reads out all roster information
        """
        self.fp = fp
        self.crew_stats = None
        self.carry_in = None
        self.roster_days = []
        self.timeZone = None
        self.month = None
        self.year = None
        self.read_data()

    def read_data(self):
        """
        Iterates thru all roster rows and collects data needed to
        create event objects.
        Data may be of three types
        - roster_day
        - heather of a roster file
        - crew_stats or information of the crew member
        """

        for row in self.fp:

            if self.carry_in is None and carryInRE.match(row):
                # Month should start in number 1 or else there is a carry in
                cin = carryInRE.match(row).groupdict()
                self.carry_in = int(cin['day']) > 1

            roster_day = rosterDayRE.match(row)
            if roster_day:
                # Found a valid row with information of a duty
                roster_day = clean(roster_day.groupdict())
                self.roster_days.append(roster_day)

            elif 'SERVICIOS' in row.upper():
                # Found the header of the roster, extract month and year
                self.set_date(row)

            elif crewstats_no_type.search(row):
                # Found all crewMember stats. Of particular importance are the
                # timeZone of the given bidLine.
                crew_stats = crewstats_no_type.search(row).groupdict()
                self.timeZone = crew_stats.pop('timeZone')
                self.crew_stats = crew_stats

            elif crewstats_with_type.search(row):
                # Found all crewMember stats. Of particular importance are the
                # timeZone of the given bidLine.
                crew_stats = crewstats_with_type.search(row).groupdict()
                self.timeZone = crew_stats.pop('timeZone')
                self.crew_stats = crew_stats

    def set_date(self, row):
        """Given a row with a ___________  MONTH YEAR format string,
        read its year and month"""
        rs = row.upper().split()
        self.year = int(rs.pop())
        self.month = rs.pop()


def clean(roster_day):
    """
        Given a roster_day as a String, clean it up and return it as a DotDict
    """
    # print("\n\nIam inside the clean(roster_day) method")
    # print("roster_day (as a Dotdict): ")
    roster_day = Dotdict(**roster_day)
    # print("\n\t\t", roster_day)
    if len(roster_day.name) == 4:
        # print("the above roster_day belongs to a Trip")
        # Found information of a trip
        # Turn all flights in this roster day into a list
        flights = airItineraryRE.finditer(roster_day.sequence)
        cleaned_seq = [Dotdict(flight.groupdict()) for flight in flights]
        # print("And the cleaned_seq from roster_day looks like this: ")
        # print("\n\t\t", cleaned_seq)
    else:
        # Found information of a ground duty
        try:
            cleaned_seq = Dotdict(itineraryRE.search(roster_day.sequence).groupdict())
        except:
            print("roster_day:")
            print(roster_day)
            print("Enter sequence for ", roster_day.name)
            sequence = input()
            roster_day.sequence = sequence
            cleaned_seq = Dotdict(itineraryRE.search(roster_day.sequence).groupdict())

    roster_day.sequence = cleaned_seq
    # print("This is how roster_day looks after being sample up: ")
    # print("\n\t\t", roster_day)
    # print("\n\n")

    return roster_day


class Liner(object):
    """´Turns a Roster Reader into a bidline"""

    # TODO: Combining two one day-spaced duties into a single Duty Day.

    def __init__(self, date_tracker, roster_days, line_type='scheduled'):
        """Mandatory arguments"""
        print("wihtin Liner datetracker ", date_tracker)
        self.date_tracker = date_tracker
        self.roster_days = roster_days
        self.itinerary_builder = ItinBuilder()
        self.line_type = line_type
        month = self.date_tracker.month
        year = self.date_tracker.year
        self.line = Line(month, year)
        self.unrecognized_events = []

    def build_line(self):
        """Returns a Line object containing all data read from the text file
        but now turned into corresponding objects"""
        trip_number_tracker = '0000'
        for rosterDay in self.roster_days:
            self.date_tracker.replace(rosterDay.day)
            if len(rosterDay.name) == 4:
                # Found trip_match information
                duty_day = self.from_flight_itinerary(rosterDay)
                trip_number = rosterDay.name
                if trip_number != trip_number_tracker:
                    # A new trip_match has been found, let's create it
                    trip = Trip(trip_number, duty_day.report)
                    trip_number_tracker = trip.number
                    trip.append(duty_day)
                    self.line.append(trip)
                else:
                    # Still the same trip_match
                    trip = self.line.duties[-1]
                    previous_duty_day = trip[-1]
                    rest = duty_day.report - previous_duty_day.release
                    # Checking for events worked in different calendar days but belonging to the same duty day
                    if rest.total_seconds() <= rules.MINIMUM_REST_TIME:
                        trip.pop()
                        duty_day.merge(previous_duty_day)
                    trip.append(duty_day)
                    self.line.duties[-1] = trip

            elif rosterDay.name in ['VA', 'X', 'XX', 'TO']:
                marker = self.from_marker(rosterDay)
                self.line.append(marker)
            elif rosterDay.name == 'RZ':
                # We don't need this marker
                pass
            elif len(rosterDay.name) == 2:
                duty_day = self.from_ground_itinerary(rosterDay)
                self.line.append(duty_day)
            else:
                self.unrecognized_events.append(rosterDay.name)

    def from_flight_itinerary(self, roster_day):
        """Given a group of duties, add them to a DutyDay"""
        duty_day = DutyDay()
        for itin in roster_day.sequence:
            itinerary = self.itinerary_builder.convert(self.date_tracker.dated, itin.begin, itin.end)
            origin = temp_airports_dict.setdefault(itin.origin, Airport(itin.origin))
            destination = temp_airports_dict.setdefault(itin.destination, Airport(itin.destination))
            if self.line_type == 'scheduled':
                f = Flight(name=itin.name, origin=origin, destination=destination,
                           scheduled_itinerary=itinerary)
            else:
                f = Flight(name=itin.name, origin=origin, destination=destination,
                           actual_itinerary=itinerary)
            duty_day.append(f)
        return duty_day

    def from_ground_itinerary(self, rD):
        """Given a ground duty, add it to a DutyDay"""
        duty_day = DutyDay()
        itinerary = self.itinerary_builder.convert(self.date_tracker.dated,
                                                   rD.sequence['begin'],
                                                   rD.sequence['end'])
        origin = temp_airports_dict['MEX']
        destination = temp_airports_dict['MEX']
        if self.line_type == 'scheduled':
            i = GroundDuty(name=rD.name, scheduled_itinerary=itinerary, origin=origin, destination=destination)
        else:
            i = GroundDuty(rD.name, None, itinerary)
        duty_day.append(i)
        return duty_day

    def from_marker(self, rD):
        """return marker data, marker's don't have credits """
        itinerary = self.itinerary_builder.convert(self.date_tracker.dated,
                                                   rD.sequence['begin'],
                                                   rD.sequence['end'])
        if self.line_type == 'scheduled':
            marker = Marker(rD.name, itinerary)
        else:
            marker = Marker(rD.name, None, itinerary)
        return marker


class ItinBuilder(object):
    """Given string parameters, this adapter will return a dictionary containing the corresponding
    parameters turned into objects, thus creating Itinerary objects from strings
    in any given timezone."""

    def __init__(self, airport_where_time=None):
        """
        airport_where_time asks for the 3-letter airport code of the timeZone, defaults to None.
        A None value, indicates local times
        """
        # self.dataTZ = citiesDic[airport_where_time].timezone if airport_where_time else None
        self.dataTZ = airport_where_time

    def convert(self, dated, begin, end):
        """date should  be a datetime object
        begin and end should have a %H%M (2345) format
        origin and destination are three-letter airport codes
        :type date: datetime.date"""

        begin, end = self.given_time_zone(dated, begin, end)
        return Itinerary(begin, end)

    @staticmethod
    def given_time_zone(dated, begin, end):
        """Generate begin and end datetime objects unaware"""

        formatting = '%H%M'
        begin_string = datetime.strptime(begin, formatting).time()
        begin = datetime.combine(dated, begin_string)
        end_string = datetime.strptime(end, formatting).time()
        end = datetime.combine(dated, end_string)

        if end < begin:
            end += timedelta(days=1)
        # if end_day:
        #     end.replace(day = int(end_day))

        # begin = self.dataTZ.localize(begin)
        # end = self.dataTZ.localize(end)

        return begin, end
