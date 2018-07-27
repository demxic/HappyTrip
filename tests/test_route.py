from unittest import TestCase

from model.scheduleClasses import Route, Airport


class TestRoute(TestCase):
    def setUp(self):
        self.origin = Airport('MEX')
        self.destination = Airport('JFK')
        self.route = Route('0403', self.origin, self.destination, 1)


class TestInit(TestRoute):

    def test_flight_number(self):
        self.assertEqual(self.route.name, '0403')

    def test_departure_airport(self):
        self.assertEqual(self.route.departure_airport, self.origin)

    def test_arrival_airport(self):
        self.assertEqual(self.route.arrival_airport, self.destination)

    def test_route_id(self):
        self.assertEqual(self.route._id, 1)

    def test_carrier_code(self):
        self.assertEqual(self.route.carrier_code, 'AM')