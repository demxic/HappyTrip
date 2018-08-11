"""
Created on 29/12/2015

@author: Xico

A bidline reader should return a bidline

"""
import operator
from app.AdminApp import get_route
from data.regex import crewstats_no_type, crewstats_with_type, airItineraryRE, itineraryRE, carryInRE, \
    roster_data_RE, non_trip_RE, roster_trip_RE
from model.scheduleClasses import Line, Flight, GroundDuty, DutyDay, Trip, Itinerary, Marker, Airport
from data import rules


class RosterReader(object):
    def __init__(self, content: str = None):
        """
        Receives an fp iterable and reads out all roster information
        """
        self.content = content
        self.crew_stats = None
        self.carry_in = None
        self.roster_days = []
        self.timeZone = None
        self.month = None
        self.year = None
        self.read_data()

    def read_data(self):
        """
        Search for all needed information
        Data may be of three types
        - roster_day
        - heather of a roster file
        - crew_stats or information of the crew member
        """

        roster_data = roster_data_RE.search(self.content).groupdict()
        self.month = roster_data['month']
        self.year = int(roster_data['year'])
        # Found all crewMember stats. Of particular importance are the
        # timeZone of the given bidLine.
        crew_stats = crewstats_no_type.search(roster_data['header']).groupdict()
        if not crew_stats:
            crew_stats = crewstats_with_type.search(roster_data['header']).groupdict()
        self.timeZone = crew_stats.pop('timeZone')
        self.crew_stats = crew_stats

        # Month should start in number 1 or else there is a carry in
        cin = carryInRE.search(roster_data['body'])
        first_day_in_roster = cin.groupdict()['day']
        self.carry_in = int(first_day_in_roster) > 1

        for roster_day in non_trip_RE.finditer(roster_data['body']):
            self.roster_days.append(roster_day.groupdict())

        for trip_row_match in roster_trip_RE.finditer(roster_data['body']):
            roster_day = trip_row_match.groupdict()
            flights = []
            for flight in airItineraryRE.finditer(roster_day['flights']):
                flights.append(flight.groupdict())
            roster_day['flights'] = flights
            self.roster_days.append(roster_day)

        self.roster_days.sort(key=operator.itemgetter('day'))


class Liner(object):
    """´Turns a Roster Reader into a line"""

    # TODO: Combining two one day-spaced duties into a single Duty Day.

    def __init__(self, date_tracker, roster_days, line_type='scheduled',
                 base_iata_code='MEX'):
        """Mandatory arguments"""
        print("wihtin Liner datetracker ", date_tracker)
        self.date_tracker = date_tracker
        self.roster_days = roster_days
        self.line_type = line_type
        self.base = Airport(base_iata_code)
        month = self.date_tracker.month
        year = self.date_tracker.year
        self.line = Line(month, year)
        self.unrecognized_events = []

    def build_line(self):
        """Returns a Line object containing all data read from the text file
        but now turned into corresponding objects"""
        trip_number_tracker = '0000'
        for roster_day in self.roster_days:
            self.date_tracker.replace(roster_day['day'])
            if len(roster_day['name']) == 4:
                # Found trip_match information
                duty_day = self.from_flight_itinerary(roster_day)
                trip_number = roster_day['name']
                if trip_number != trip_number_tracker:
                    # A new trip_match has been found, let's create it
                    trip = Trip(number=trip_number, dated=self.date_tracker.dated)
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

            elif roster_day['name'] in ['VA', 'X', 'XX', 'TO']:
                roster_day['begin'] = '0001'
                roster_day['end'] = '2359'
                itinerary = self.build_itinerary(roster_day)
                marker = Marker(name=roster_day['name'], itinerary=itinerary)
                self.line.append(marker)
            elif len(roster_day['name']) == 2 and roster_day['name'] != 'RZ':
                duty_day = self.from_ground_itinerary(roster_day)
                self.line.append(duty_day)
            else:
                self.unrecognized_events.append(roster_day['name'])

    def from_flight_itinerary(self, roster_day):
        """Given a group of duties, add them to a DutyDay"""
        duty_day = DutyDay()
        for flight in roster_day['flights']:
            itinerary = Itinerary.from_date_and_strings(self.date_tracker.dated,
                                                        flight['begin'], flight['end'])
            origin = Airport(flight['origin'])
            destination = Airport(flight['destination'])
            route = get_route(flight_number=flight['name'][-4:], departure_airport=origin,
                              arrival_airport=destination)
            if self.line_type == 'scheduled':
                f = Flight(route=route, scheduled_itinerary=itinerary)
            else:
                f = Flight(route=route, actual_itinerary=itinerary)
            duty_day.append(f)
        return duty_day

    def from_ground_itinerary(self, rD):
        """Given a ground duty, add it to a DutyDay"""
        duty_day = DutyDay()
        itinerary = self.build_itinerary(rD)
        route = get_route(flight_number='0000', departure_airport=self.base,
                          arrival_airport=self.base)
        if self.line_type == 'scheduled':
            i = GroundDuty(route=route, scheduled_itinerary=itinerary)
        else:
            i = GroundDuty(route=route, actual_itinerary=itinerary)
        duty_day.append(i)
        return duty_day

    def build_itinerary(self, rD):
        """return marker data, marker's don't have credits """
        try:
            begin = rD['begin']
            end = rD['end']
        except KeyError:
            begin = '0001'
            end = '2359'
            # print("Unknown begin and end times for duty")
            # print("{} {} ".format(self.date_tracker.dated, rD['name']))
            # begin, end = input("Begin and END time as HHMM HHMM ").split()
        itinerary = Itinerary.from_date_and_strings(self.date_tracker.dated, begin, end)

        return itinerary
