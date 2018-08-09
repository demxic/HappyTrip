"""The general purpose of this module is to manualy create and interact with duties from the HappyTrip module"""
from datetime import datetime, date
from model.scheduleClasses import CrewMember, Route, Airport, Itinerary, GroundDuty, Flight, Equipment, DutyDay, Trip
date_format = "%d%m%y"
time_format = "%H%M"


def create_date(date_string: str) -> date:
    """Given a string turn it into a datetime.date object
        %d Day of the month as a zero-padded decimal number.
        %m Month as a zero-padded decimal number.
        %y Year without century as a zero-padded decimal number."""
    return datetime.strptime(date_string, date_format).date()


def create_datetime() -> datetime:
    """Given a string turn it into a datetime object
        %d Day of the month as a zero-padded decimal number.
        %m Month as a zero-padded decimal number.
        %y Year without century as a zero-padded decimal number.
        %H Hour (24-hour clock) as a zero-padded decimal number.
        %M Minute as a zero-padded decimal number.
    """
    datetime_string = input("enter datetime as %d%m%y %H%M format.  v.gr.  130879 0930")
    return datetime.strptime(datetime_string, date_format + ' ' + time_format)


def create_route() -> Route:
    route_string = input("Enter route as FLT ORG DES, v.gr  E2 MEX MEX    or   0403 MEX JFK   or   0106 MEX GDL")
    name, departure_airport, arrival_airport = route_string.split()
    route = Route(flight_number=name, departure_airport=Airport(departure_airport),
                  arrival_airport=Airport(arrival_airport))
    return route


def create_itinerary() -> Itinerary:
    """Given an itinerary as a string"""
    print("begin datetime for itinerary, please ", end=" ")
    begin_datetime = create_datetime()
    print("  end datetime for itinerary, please ", end=" ")
    end_datetime = create_datetime()
    return Itinerary(begin=begin_datetime, end=end_datetime)


def create_event_dict() -> dict:
    """Given an event as a string turn it into a dictionary with fields:
        route, scheduled_itinerary, actual_itinerary, position

        v.gr  100818 E3 MEX 0823 1345
        route = E3 MEX MEX
        scheduled_itinerary = 100813 0823 1345
        actual_itinerary = None
        position = SOB or EJE

        Note: While creating an event that is a flight to be, DH condition should not be marked within route name
    """

    event_dict = dict()
    event_dict['route'] = create_route()

    answer = input("Input a scheduled itinerary? Y/N :").capitalize()
    if answer[0] != 'N':
        print("Enter scheduled itinerary : ")
        event_dict['scheduled_itinerary'] = create_itinerary()
    else:
        event_dict['scheduled_itinerary'] = None

    answer = input("Input an actual itinerary? Y/N :").capitalize()
    if answer[0] != 'N':
        print("Enter actual itinerary : ")
        event_dict['actual_itinerary'] = create_itinerary()
    else:
        event_dict['actual_itinerary'] = None

        event_dict['position'] = input("Is this an EJE or SOB position? ").capitalize()

    return event_dict


def create_ground_duty() -> GroundDuty:
    """Given an event_dict as a dict, turn it into a Ground Duty object
            ground_duty_string = 100818 E3 MEX 0823 1345"""
    return GroundDuty(**create_event_dict())
    # return GroundDuty(route=event_dict['route'], scheduled_itinerary=event_dict['scheduled_itinerary'],
    #                   actual_itinerary=event_dict['actual_itinerary'], position=event_dict['position'])


def create_flight() -> Flight:
    """Given a Flight as a string turn it into an object
            flight_string = 100818 E3 MEX 0823 1345
        """
    event_dict = create_event_dict()
    dh = input("Is this a DH flight? Y/N ").capitalize()[0]
    if dh.startswith('Y'):
        dh = True
    else:
        dh = False
    event_dict['dh'] = dh
    event_dict['equipment'] = Equipment(input("What is the 3 letter code for the aircraft flown?  "))
    flight = Flight(**event_dict)

    return flight


def create_duty_day() -> DutyDay:
    """Enter events into a duty day, one by one"""
    answer = 'Y'
    event = None
    duty_day = DutyDay()
    while answer == 'Y':
        option = input("Enter F for a new FLIGHT or G for a new GROUND DUTY: ").capitalize()
        if option == 'F':
            event = create_flight()
        elif option == 'G':
            event = create_ground_duty()
        else:
            r = input("Invalid option")

        if event:
            duty_day.append(event)
            print()
            print(duty_day)
            print()
        answer = input("Would you like to add a new event to duty day?  y/n: ").capitalize()
        print()
        event = None

    return duty_day


def create_trip() -> Trip:
    """ Create a trip and enter duty days one by one """
    answer = 'Y'
    trip_number, trip_date = input("Enter trip_number and date v.gr 7009 130818    #").split()
    trip_dated = create_date(trip_date)
    trip = Trip(number=trip_number, dated=trip_dated)
    while answer == 'Y':
        duty_day = create_duty_day()
        trip.append(duty_day)
        answer = input("Would you like to add a new duty_day to trip?  y/n: ").capitalize()
        print()
    return trip