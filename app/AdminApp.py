from datetime import datetime
import sys

from data.database import Database
from data.regex import trip_RE, dutyday_RE, flights_RE
from model.scheduleClasses import Airport, Trip, Route

Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")
source = "C:\\Users\\Xico\\PycharmProjects\\HappyTrip\\data\\iata_tzmap.txt"
pbs_path = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\PBS\\"
file_name = "201806 PBS todos los vuelos ESB.txt"
datetime_format = "%d%b%Y%H:%M"
session_airports = {}
session_routes = dict()


def get_route(name, origin, destination):
    route_key = name + '' + origin + '' + destination
    if route_key not in session_routes.keys():
        # Route has not been loaded from the DB
        route = Route.load_from_db_by_fields(flight_number=name,
                                             departure_airport=origin,
                                             arrival_airport=destination)
        if not route:
            # Route must be created and stored into DB
            route = Route(name, origin, destination)
            route.save_to_db()
            session_routes[route_key] = route
    else:
        route = session_routes[route_key]
    return route


def get_airport(city):
    airport = session_airports.get(city)
    if airport is None:
        airport = Airport.load_from_db_by_iata_code(city)
    session_airports[city] = airport
    return airport


with open(pbs_path + file_name) as fp:
    content = fp.read()
    for trip_match in trip_RE.finditer(content):
        trip_dict = trip_match.groupdict()
        date_string = trip_dict['dated'] + trip_dict['check_in']
        dtracker = datetime.strptime(date_string, datetime_format)
        trip = Trip(trip_dict['number'], dtracker.date())

        for dutyday_match in dutyday_RE.finditer(trip_dict['duties']):
            duty_day_dict = dutyday_match.groupdict()
            for flight_match in flights_RE.finditer(duty_day_dict['flights']):

                flight_dict = flight_match.groupdict()

                # First section gets airports
                airport = get_airport(flight_dict['destination'])

                # Second section gets routes
                # Because some flights begin with a DH, we should only take into consideration the last 4 digits
                route = get_route(flight_dict['name'][-4:], flight_dict['origin'], flight_dict['destination'])

                # Third section gets Flights
                carrier_code = 'AM'
                if 'DH' in flight_dict['name']:
                    if flight_dict['equipment'] == 'DHD':
                        flight_dict['equipment'] = 'EMB'
                        carrier_code = '6D'
                    flight_dict['name'] = flight_dict['name'][2:]
                    # print("{} flight in {} equipment".format(flight_dict['name'], flight_dict['equipment']))

for route in session_routes.values():
    print(route)
