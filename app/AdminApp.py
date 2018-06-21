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
pbs_path = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\PBS\\"
file_name = "201806 PBS todos los vuelos ESB.txt"
session_airports = dict()
session_routes = dict()
session_equipments = dict()


def get_airport(city):
    airport = session_airports.get(city)
    if airport is None:
        airport = Airport.load_from_db_by_iata_code(city)
    session_airports[city] = airport
    return airport


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


def get_equipment(eq):
    equipment = session_equipments.get(eq)
    if equipment is None:
        equipment = Equipment.load_from_db_by_code(eq)
        if not equipment:
            cabin_members = input("Minimum cabin members for a {} ".format(eq))
            equipment = Equipment(eq, cabin_members)
            equipment.save_to_db()
        session_airports[eq] = equipment
    return equipment


def get_flight(dt_tracker, flight_dict, postpone):
    # First:  get the route
    # take into consideration the last 4 digits Because some flights start with 'DH'
    route = get_route(flight_dict['name'][-4:], flight_dict['origin'], flight_dict['destination'])

    # Second: We need the airline code
    carrier_code = get_carrier(flight_dict)

    # Third : Find the flight in the DB
    begin = copy(dt_tracker.dt)
    flight = Flight.load_from_db_by_fields(airline_iata_code=carrier_code,
                                           scheduled_departure=begin,
                                           route=route)
    # Fourth : Create and store flight since it was not found in the DB
    if not flight:
        blk = flight_dict['blk']
        if blk == '0000':
            if postpone:
                return None
            else:
                print("    FLT {} {} {} {} {} {} ".format(dt_tracker.date, flight_dict['name'],
                                                      flight_dict['origin'], flight_dict['begin'],
                                                      flight_dict['destination'], flight_dict['end']))
                blk = input("    unable to determine DH time, insert blk time manually as HHMM format ")
        td = dt_tracker.forward(blk)
        itinerary = Itinerary.from_timedelta(begin=begin, a_timedelta=td)
        equipment = get_equipment(flight_dict['equipment'])
        flight = Flight(route=route, scheduled_itinerary=itinerary,
                        equipment=equipment, carrier=carrier_code)
        flight.save_to_db()
    else:
        dt_tracker.forward(str(flight.duration))
    flight.name = flight_dict['name']
    return flight


def get_carrier(flight_dict):
    carrier_code = 'AM'
    code = flight_dict['name'][0:2]
    if code.startswith('DH'):
        #Found an AM or 6D flight
        if flight_dict['equipment'] == 'DHD':
            carrier_code = '6D'
    elif not code.isdigit():
        # Found a new airline
        carrier_code = code
    return carrier_code


def get_duty_day(dt_tracker, duty_day_dict, postpone):
    dt_tracker.start()
    layover_duration = duty_day_dict['layover_duration'] if duty_day_dict['layover_duration'] else '0000'
    dictionary_flights = [f.groupdict() for f in flights_RE.finditer(duty_day_dict['flights'])]

    # The last flight in a duty_day must be re-arranged
    duty_day_dict['rls'] = dictionary_flights[-1]['blk']
    dictionary_flights[-1]['blk'] = dictionary_flights[-1]['turn']
    dictionary_flights[-1]['turn'] = '0000'
    duty_day = DutyDay()

    for flight_dict in dictionary_flights:
        flight = get_flight(dt_tracker, flight_dict, postpone)
        if flight:
            duty_day.append(flight)
            dt_tracker.forward(flight_dict['turn'])
        else:
            return None

    dt_tracker.release()
    dt_tracker.forward(layover_duration)
    return duty_day


def get_trip(trip_dict, postpone):
    dt_tracker = DateTimeTracker(trip_dict['dated'] + trip_dict['check_in'])
    trip = Trip(number=trip_dict['number'], dated=dt_tracker.date)
    print("Trip {} dated {}".format(trip.number, dt_tracker.date))

    for duty_day_match in dutyday_RE.finditer(trip_dict['duties']):
        duty_day = get_duty_day(dt_tracker, duty_day_match.groupdict(), postpone)
        # Assert that duty day was built properly

        if duty_day:
            trip.append(duty_day)
            if str(duty_day.duration) != duty_day_match.groupdict()['dy']:
                print("Something went wrong with this duty day")
                print(duty_day)
                print("Expected daily time ", duty_day_match.groupdict()['dy'])
        else:
            return None

    return trip


# with open(pbs_path + file_name) as fp:
#     content = fp.read()
unsaved_trips = []
trips_created = 0
for trip_match in trip_RE.finditer(content):
    trip = get_trip(trip_match.groupdict(), postpone=True)
    if trip:
        trip.save_to_db()
        trips_created += 1
        print(trip)
    else:
        unsaved_trips.append(trip_match.groupdict())


print("{} unbuilt trips after fist run ".format(len(unsaved_trips)))
for trip_dict in unsaved_trips:
    print(trip_dict)

print("Building unsaved_trips :")
for trip_dict in unsaved_trips:
    trip = get_trip(trip_dict, postpone=False)
    if trip:
        trip.save_to_db()
        trips_created += 1
        print(trip)
    else:
        print("trip {} dated {} cannot be stored ".format(trip.number, trip.dated))

print("Total trips processed = {}".format(trips_created))