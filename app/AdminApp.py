import json
import pickle
from copy import copy
from datetime import datetime, timedelta, date
import sys

from data.database import Database
from data.regex import trip_RE, dutyday_RE, flights_RE
from model.scheduleClasses import Airport, Trip, Route, Equipment, Flight, Itinerary, DutyDay
from model.timeClasses import DateTimeTracker

content = """
# 3431 CHECK IN AT 20:55
30JUN2018
DATE RPT FLIGHT DEPARTS ARRIVES RLS BLK TURN EQ
30JUN 2055 0194 MEX 2155 TIJ 2335 0340 0046 737
DH0111 TIJ 0021 GDL 0519 0549 0000 737
GDL 26:51 0340BL -175CRD 0205TL 0854DY
02JUL 0840 0782 GDL 0940 LAX 1110 1140 0330 38A
LAX 11:35 0330BL -370CRD 0000TL 0500DY
03JUL 2315 0785 LAX 0015 GDL 0531 0601 0316 38A
GDL 23:29 0316BL -356CRD 0000TL 0446DY
04JUL 0530 0770 GDL 0630 TIJ 0731 0301 0050 38A
0773 TIJ 0821 GDL 1330 0309 0131 38A
DH0253 GDL 1501 MEX 1630 1700 0000 7S8
0610BL -650CRD 0000TL 1130DY
TOTALS 2:05TL 2:05BL 00:00CR 92:05TAFB
# 4047 CHECK IN AT 20:00
08JUN2018
DATE RPT FLIGHT DEPARTS ARRIVES RLS BLK TURN EQ
08JUN 2000 0956 MEX 2100 MTY 2245 2315 0145 7S8
MTY 30:40 0145BL 0000CRD 0145TL 0315DY
10JUN 0555 0905 MTY 0655 MEX 0830 0135 0250 7S8
0543 MEX 1120 CUN 1337 0217 0048 7S8
0592 CUN 1425 MEX 1655 1725 0230 7S8
0622BL 0000CRD 0622TL 1130DY
TOTALS 8:07TL 8:07BL 00:00CR 45:25TAFB
# 4048 CHECK IN AT 08:40
06JUN2018
DATE RPT FLIGHT DEPARTS ARRIVES RLS BLK TURN EQ
06JUN 0840 1120 MEX 0940 GDL 1104 0124 0056 38A
0178 GDL 1200 TIJ 1303 0303 0057 38A
DH0179 TIJ 1400 GDL 1858 1928 0000 38A
GDL 13:10 0427BL 0258CRD 0725TL 1048DY
07JUN 0838 0782 GDL 0938 LAX 1110 1140 0332 38A
LAX 11:35 0332BL 0000CRD 0332TL 0502DY
08JUN 2315 0785 LAX 0015 GDL 0534 0319 0115 38A
DH0239 GDL 0649 MEX 0815 0845 0000 7S8
0319BL 0126CRD 0445TL 0730DY
TOTALS 15:42TL 11:18BL 04:24CR 48:05TAFB
# 4049 CHECK IN AT 12:30
16JUN2018
DATE RPT FLIGHT DEPARTS ARRIVES RLS BLK TURN EQ
16JUN 1230 1176 MEX 1330 TIJ 1511 0341 0059 7S8
1177 TIJ 1610 MEX 2142 2212 0332 7S8
0713BL 0000CRD 0713TL 0942DY
TOTALS 7:13TL 7:13BL 00:00CR 9:42TAFB
# 4049 CHECK IN AT 12:30
23JUN2018
DATE RPT FLIGHT DEPARTS ARRIVES RLS BLK TURN EQ
23JUN 1230 1176 MEX 1330 TIJ 1511 0341 0059 737
1177 TIJ 1610 MEX 2142 2212 0332 737
0713BL 0000CRD 0713TL 0942DY
TO"""

Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")
source = "C:\\Users\\Xico\\PycharmProjects\\HappyTrip\\data\\iata_tzmap.txt"
pbs_path = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\PBS\\2018 PBS\\201805 PBS\\"
# file_names = ["201806 PBS EJE.txt"]
file_names = ["201805 PBS EJE.txt", "201805 PBS SOB.txt", "201805 PBS SOB B.txt"]
pickled_unsaved_trips_file = 'pickled_unsaved_trips'
session_airports = dict()
session_routes = dict()
session_equipments = dict()

def get_airport(city):
    airport = session_airports.get(city)
    if not airport:
        airport = Airport.load_from_db_by_iata_code(city)
    session_airports[city] = airport
    return airport


def get_route(flight_number: str, departure_airport: Airport, arrival_airport: Airport) -> Route:
    route_key = flight_number + departure_airport.iata_code + arrival_airport.iata_code
    if route_key not in session_routes.keys():
        # Route has not been loaded from the DB
        route = Route.load_from_db_by_fields(flight_number=flight_number,
                                             departure_airport=departure_airport.iata_code,
                                             arrival_airport=arrival_airport.iata_code)
        if not route:
            # Route must be created and stored into DB
            route = Route(flight_number=flight_number, departure_airport=departure_airport,
                          arrival_airport=arrival_airport)
            route.save_to_db()
            session_routes[route_key] = route
    else:
        route = session_routes[route_key]
    return route


def get_equipment(eq) -> Equipment:
    equipment = session_equipments.get(eq)
    if not equipment:
        equipment = Equipment.load_from_db_by_code(eq)
        if not equipment:
            cabin_members = input("Minimum cabin members for a {} ".format(eq))
            equipment = Equipment(eq, cabin_members)
            equipment.save_to_db()
        session_equipments[eq] = equipment
    return equipment


class ZeroBlockTime(Exception):
    pass


class UndefinedBlockTime(Exception):
    pass


class DutyDayBlockError(Exception):

    def __init__(self, duty_day_dict: dict, duty_day: DutyDay) -> None:
        super().__init__("DutyDay's expected daily time {} is different from actual {}".format(duty_day_dict['dy'],
                                                                                               duty_day.duration))
        self.duty_day_dict = duty_day_dict
        self.duty_day = duty_day

    def delete_invalid_flights(self):
        found_one_after_dh = False
        for flight in self.duty_day.events:
            if not flight.name.isnumeric() or found_one_after_dh:
                # TODO : Instead of deleting flight, try erasing only the inconsistent data
                print("Dropping from DataBase flight: {} ".format(flight))
                flight.delete()
                found_one_after_dh = True

    def correct_invalid_events(self):
        for flight in self.duty_day.events:
            print(flight)
            r = input("Is flight properly built? y/n").capitalize()
            if 'N' in r:
                itinerary_string = input("Enter itinerary as string (date, begin, blk) 31052018 2206 0122 ")
                itinerary = Itinerary.from_string(itinerary_string)
                flight.scheduled_itinerary = itinerary
                flight.update()


class TripBlockError(Exception):

    def __init__(self, expected_block_time, trip):
        super().__init__("Trip's expected block time {} is different from actual {}".format(expected_block_time,
                                                                                               trip.duration))
        self.expected_block_time = expected_block_time
        self.trip = trip

    def delete_invalid_duty_days(self):
        pass


class UnbuiltTripError(Exception):
    pass


def get_flight(dt_tracker: DateTimeTracker, flight_dict: dict,
               postpone: bool, suggested_blk: str) -> Flight:
    # 1. Get the route
    # take into consideration the last 4 digits Because some flights start with 'DH'
    origin = get_airport(flight_dict['origin'])
    destination = get_airport(flight_dict['destination'])
    route = get_route(flight_dict['name'][-4:], origin, destination)

    # 2. We need the airline code
    carrier_code = get_carrier(flight_dict)

    # 3. Find the flight in the DB
    begin = copy(dt_tracker.dt)
    flight = Flight.load_from_db_by_fields(airline_iata_code=carrier_code,
                                           scheduled_departure=begin,
                                           route=route)

    # 4. Create and store flight if not found in the DB
    if not flight:
        try:
            if flight_dict['blk'] != '0000':
                # 4.a Found a regular flight, create it
                td = dt_tracker.forward(flight_dict['blk'])
                itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
            elif suggested_blk != '0000' and suggested_blk.isnumeric():
                # 4.b Found a DH flight in a duty day with a suggested block time
                td = dt_tracker.forward(suggested_blk)
                itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
                if not itinerary.in_same_month():
                    # Flight reaches next month and therefore it's block time cannot be determined
                    dt_tracker.backward(suggested_blk)
                    raise UndefinedBlockTime()
            else:
                raise UndefinedBlockTime()

        except UndefinedBlockTime:

            # 4.d Unable to determine flight blk, must enter it manually
            if postpone:
                raise UnbuiltTripError()
            else:
                print("FLT {} {} {} {} {} {} ".format(dt_tracker.date, flight_dict['name'],
                                                      flight_dict['origin'], flight_dict['begin'],
                                                      flight_dict['destination'], flight_dict['end']))
                print("unable to determine DH time.")
                print("")
                blk = input("Insert time as HHMM format :")
                td = dt_tracker.forward(blk)
                itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)

        equipment = get_equipment(flight_dict['equipment'])
        flight = Flight(route=route, scheduled_itinerary=itinerary,
                        equipment=equipment, carrier=carrier_code)
        flight.save_to_db()
    else:
        dt_tracker.forward(str(flight.duration))
    flight.dh = not flight_dict['name'].isnumeric()
    return flight


def get_carrier(flight_dict):
    carrier_code = 'AM'
    code = flight_dict['name'][0:2]
    if code.startswith('DH'):
        # Found an AM or 6D flight
        if flight_dict['equipment'] == 'DHD':
            carrier_code = '6D'
    elif not code.isdigit():
        # Found a new airline
        carrier_code = code
    return carrier_code


def get_duty_day(dt_tracker, duty_day_dict, postpone):
    dt_tracker.start()
    duty_day = DutyDay()

    for flight_dict in duty_day_dict['flights']:
        flight = get_flight(dt_tracker, flight_dict, postpone, suggested_blk=duty_day_dict['crd'])
        if flight:
            duty_day.append(flight)
            dt_tracker.forward(flight_dict['turn'])
    dt_tracker.release()
    dt_tracker.forward(duty_day_dict['layover_duration'])

    # Assert that duty day was built properly
    if str(duty_day.duration) != duty_day_dict['dy']:
        raise DutyDayBlockError(duty_day_dict, duty_day)

    return duty_day


def get_trip(trip_dict: dict, postpone: bool) -> Trip:
    dt_tracker = DateTimeTracker(trip_dict['date_and_time'])
    trip = Trip(number=trip_dict['number'], dated=dt_tracker.date)

    for json_dd in trip_dict['duty_days']:
        try:
            duty_day = get_duty_day(dt_tracker, json_dd, postpone)
            trip.append(duty_day)

        except DutyDayBlockError as e:
            print("For trip {0} dated {1}, ".format(trip_dict['number'], trip_dict['dated']), end=' ')
            print("found inconsistent duty day : ")
            print("       ", e.duty_day)
            if postpone:
                e.delete_invalid_flights()
                raise UnbuiltTripError
            else:
                print("... Correcting for inconsistent duty day: ")
                e.correct_invalid_events()
                print("Corrected duty day")
                print(e.duty_day)
                trip.append(e.duty_day)

    return trip


def get_json_duty_day(duty_day_dict: dict) -> dict:
    """
    Given a dictionary containing random duty_day data, turn it into a dictionary
    that can be stored as a json format
    """
    duty_day_dict['layover_duration'] = duty_day_dict['layover_duration'] if duty_day_dict['layover_duration'] else '0000'

    # The last flight in a duty_day must be re-arranged
    dictionary_flights = [f.groupdict() for f in flights_RE.finditer(duty_day_dict['flights'])]
    duty_day_dict['rls'] = dictionary_flights[-1]['blk']
    dictionary_flights[-1]['blk'] = dictionary_flights[-1]['turn']
    dictionary_flights[-1]['turn'] = '0000'

    duty_day_dict['flights'] = dictionary_flights

    return duty_day_dict


def get_json_trip(trip_dict: dict) -> dict:
    """
    Given a dictionary containing random trip data, turn it into a dictionary
    that can be stored as a json format
    """
    trip_dict['date_and_time'] = trip_dict['dated'] + trip_dict['check_in']
    dds = list()

    for duty_day_match in dutyday_RE.finditer(trip_dict['duty_days']):
        duty_day = get_json_duty_day(duty_day_match.groupdict())
        dds.append(duty_day)
    trip_dict['duty_days'] = dds

    return trip_dict


class DutyInsideTripError(object):
    pass


class Menu:
    """Display a menu and respond to choices when run"""

    def __init__(self):
        self.choices = {
            "1": self.read_trips_file,
            "2": self.figure_out_unsaved_trips,
            "3": self.search_for_trip,
            "10": self.quit}

    @staticmethod
    def display_menu():
        print('''
        Orgutrip Menu

        1. Leer los archivos con los trips.
        2. Trabajar con los trips que no pudieron ser creados.
        3. Buscar un trip en especìfico.
        10. Quit
        ''')

    def run(self):
        """Display the menu and respond to choices"""
        while True:
            self.display_menu()
            choice = input("¿Qué deseas realizar?: ")
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print("{0} is not a valid choice".format(choice))

    def read_trips_file(self):
        unstored_trips = list()
        for file_name in file_names:
            # 1. Read in and clean the txt.file
            with open(pbs_path + file_name, 'r') as fp:
                print("\n file name : ", file_name)
                position = input("Is this a PBS file for EJE or SOB? ")
                json_trips = self.create_json_trips(fp.read())
                pending_trips = self.create_trips(json_trips, position, postpone=True)
                unstored_trips.extend(pending_trips)
        outfile = open(pbs_path + pickled_unsaved_trips_file, 'wb')
        pickle.dump(unstored_trips, outfile)
        outfile.close()


    def create_json_trips(self, content: str) -> dict:
        """Given a string content return each json_trip within"""
        # 1. Turn each read trip into a clearer dictionary format
        for trip_match in trip_RE.finditer(content):
            json_trip = get_json_trip(trip_match.groupdict())
            yield json_trip

    def create_trips(self, json_trips, position, postpone=True):
        # 2. Turn each trip_dict into a Trip object
        json_trip_count = 0
        unstored_trips = list()
        for json_trip in json_trips:
            if 'position' not in json_trip:
                json_trip['position'] = position
            json_trip_count += 1
            try:
                # if json_trip['number'] == '3760':
                #     input("Enter para continuar")
                trip = get_trip(json_trip, postpone)
                if trip.duration.no_trailing_zero() != json_trip['tafb']:
                    raise TripBlockError(json_trip['tafb', trip])

            except TripBlockError as e:
                # TODO : Granted, there's a trip block error, what actions should be taken to correct it? (missing)
                print("trip {0.number} dated {0.dated} {0.duaration.no_trailing_zero()}"
                      "does not match expected TAFB {1}".format(e.trip, e.expected_block_time))
                print("Trip {0} dated {1} unsaved!".format(json_trip['number'], json_trip['dated']))
                unstored_trips.append(json_trip)

            except UnbuiltTripError:
                print("Trip {0} dated {1} unsaved!".format(json_trip['number'], json_trip['dated']))
                unstored_trips.append(json_trip)

            else:
                print("Trip {0.number} dated {0.dated} saved".format(trip))
                trip.position = position
                trip.save_to_db()

        print("{} json trips found ".format(json_trip_count))
        return unstored_trips


    def figure_out_unsaved_trips(self):
        infile = open(pbs_path + pickled_unsaved_trips_file, 'rb')
        unstored_trips = pickle.load(infile)
        print("Building {} unsaved_trips :".format(len(unstored_trips)))
        # 1. Let us go over all trips again, some might now be discarded
        irreparable_trips = self.create_trips(unstored_trips, None, postpone=False)
        print(" {} unsaved_trips".format(len(irreparable_trips)))

    def search_for_trip(self):
        entered = input("Enter trip/dated to search for ####/DDMMMYYYY")
        trip_id, trip_dated = entered.split('/')
        trip = Trip.load_by_id(trip_id, trip_dated)
        print(trip)

    def quit(self):
        print("adiós")
        sys.exit(0)

if __name__ == '__main__':
    Menu().run()
