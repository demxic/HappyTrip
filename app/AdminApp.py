import json
import pickle
from copy import copy
from datetime import datetime, timedelta, date
import sys

from data.database import Database
from data.regex import trip_RE, dutyday_RE, flights_RE, reserve_RE
from model.scheduleClasses import Airport, Trip, Route, Equipment, Flight, Itinerary, DutyDay, GroundDuty
from model.timeClasses import DateTimeTracker

Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")
source = "C:\\Users\\Xico\\PycharmProjects\\HappyTrip\\data\\iata_tzmap.txt"
pbs_path = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\PBS\\2018 PBS\\201806 PBS\\"
# file_names = ["201806 PBS EJE.txt"]
file_names = ["201806 PBS vuelos EJE.txt", "201806 PBS vuelos SOB A.txt", "201806 PBS vuelos SOB B.txt"]
reserve_files = ["201806 PBS reservas EJE.txt", "201806 PBS reservas SOB.txt"]
pickled_unsaved_trips_file = 'pickled_unsaved_trips'
session_routes = dict()
session_equipments = dict()


#
# def get_airport(city):
#     airport = session_airports.get(city)
#     if not airport:
#         airport = Airport.load_from_db_by_iata_code(city)
#     session_airports[city] = airport
#     return airport


def get_route(name: str, origin: Airport, destination: Airport) -> Route:
    route_key = name + origin.iata_code + destination.iata_code
    if route_key not in Route._routes:
        # Route has not been loaded from the DB
        route = Route.load_from_db_by_fields(name=name,
                                             origin=origin,
                                             destination=destination)
        if not route:
            # Route must be created and stored into DB
            route = Route(name=name, origin=origin, destination=destination)
            route.save_to_db()
    else:
        route = Route._routes[route_key]
    return route


#
# def get_equipment(eq) -> Equipment:
#     equipment = session_equipments.get(eq)
#     if not equipment:
#         equipment = Equipment.load_from_db_by_code(eq)
#         if not equipment:
#             cabin_members = input("Minimum cabin members for a {} ".format(eq))
#             equipment = Equipment(eq, cabin_members)
#             equipment.save_to_db()
#         session_equipments[eq] = equipment
#     return equipment


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
                flight.update_to_db()


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
    # origin = get_airport(flight_dict['origin'])
    # destination = get_airport(flight_dict['destination'])
    origin = Airport(flight_dict['origin'])
    destination = Airport(flight_dict['destination'])
    route = get_route(flight_dict['name'][-4:], origin, destination)

    # 2. We need the airline code
    carrier_code = get_carrier(flight_dict)

    # 3. Find the flight in the DB
    begin = copy(dt_tracker.dt)
    flight = Flight.load_from_db_by_fields(airline_iata_code=carrier_code,
                                           scheduled_begin=begin,
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

        equipment = Equipment(flight_dict['equipment'])
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
    duty_day_dict['layover_duration'] = duty_day_dict['layover_duration'] if duty_day_dict[
        'layover_duration'] else '0000'

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
            "4": self.read_reserve_file,
            "10": self.quit}

    @staticmethod
    def display_menu():
        print('''
        Orgutrip Menu

        1. Leer los archivos con los trips.
        2. Trabajar con los trips que no pudieron ser creados.
        3. Buscar un trip en especìfico.
        4. Leer los archivos con las reservas.
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
                position = input("Is this a PBS file for EJE or SOB? ").upper()
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
                    print(json_trip)
                    raise TripBlockError(json_trip['tafb'], trip)

            except TripBlockError as e:
                # TODO : Granted, there's a trip block error, what actions should be taken to correct it? (missing)
                print("trip {0.number} dated {0.dated} {0.duration}"
                      " does not match expected TAFB {1}".format(e.trip, e.expected_block_time))
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
        outfile = open(pbs_path + pickled_unsaved_trips_file, 'wb')
        pickle.dump(irreparable_trips, outfile)
        outfile.close()

    def search_for_trip(self):
        entered = input("Enter trip/dated to search for ####/YYYY-MM-DD ")
        trip_id, trip_dated = entered.split('/')
        trip = Trip.load_by_id(trip_id, trip_dated)
        print(trip)

    def read_reserve_file(self):
        for file_name in reserve_files:
            # 1. Read in and clean the txt.file
            with open(pbs_path + file_name, 'r') as fp:
                print("\n file name : ", file_name)
                position = input("Is this a PBS file for EJE or SOB? ").capitalize()
                year = "2018"
                for reserve_match in reserve_RE.finditer(fp.read()):
                    reserve_dict = reserve_match.groupdict()
                    reserve_dict['year'] = year
                    reserve = self.create_reserve(reserve_dict)
                    reserve.position = position
                    reserve.save_to_db()

    def create_reserve(self, rd):
        formatting = '%d%b%Y%H%M'
        begin = datetime.strptime(rd['date'] + rd['year'] + rd['begin'], formatting)
        end = datetime.strptime(rd['date'] + rd['year'] + rd['end'], formatting)
        if end < begin:
            end = end - timedelta(days=1)
        itinerary = Itinerary(begin, end)
        origin = Airport('MEX')
        destination = Airport('MEX')
        route = get_route('0000', origin, destination)
        route.flight_number = rd['name']
        return GroundDuty(route=route, scheduled_itinerary=itinerary)

    def quit(self):
        print("adiós")
        sys.exit(0)


if __name__ == '__main__':
    Menu().run()
