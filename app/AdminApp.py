from datetime import datetime
import sys

from data.database import Database
from data.regex import trip_RE, dutyday_RE, flights_RE
from model.scheduleClasses import Airport, Trip

Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")
source = "C:\\Users\\Xico\\PycharmProjects\\HappyTrip\\data\\iata_tzmap.txt"
pbs_path = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\PBS\\"
file_name = "201806 PBS todos los vuelos ESB.txt"
datetime_format = "%d%b%Y%H:%M"
session_airports = {}

with open(pbs_path + file_name) as fp:
    content = fp.read()
    for trip_match in trip_RE.finditer(content):
        trip_dict = trip_match.groupdict()
        date_string = trip_dict['dated']+trip_dict['check_in']
        dtracker = datetime.strptime(date_string, datetime_format)
        trip = Trip(trip_dict['number'], dtracker.date())

        for dutyday_match in dutyday_RE.finditer(trip_dict['duties']):
            duty_day_dict = dutyday_match.groupdict()
            for flight_match in flights_RE.finditer(duty_day_dict['flights']):
                flight_dict = flight_match.groupdict()
                city = flight_dict['destination']
                airport = session_airports.get(city)
                if airport is None:
                    airport = Airport.load_from_db_by_iata_code(city)
                session_airports[city] = airport





