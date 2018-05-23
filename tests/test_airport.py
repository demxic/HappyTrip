import unittest

from data.database import Database
from model.scheduleClasses import Airport

Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")


class TestAirport(unittest.TestCase):
    def setUp(self):
        self.airport = Airport(iata_code='MEX', timezone='America/Mexico_City', viaticum='low_cost')


class TestInit(TestAirport):
    def test_iata_code(self):
        self.assertEqual(self.airport.iata_code, 'MEX')

    def test_timezone(self):
        self.assertEqual(self.airport.timezone, 'America/Mexico_City')

    def test_viaticum(self):
        self.assertEqual(self.airport.viaticum, 'low_cost')


class TestDataBase(TestAirport):
    # def test_store_airport(self):
    #     self.airport.save_to_db()

    def test_retrieve_airport(self):
        airport = Airport.load_from_db_by_iata_code('MEX')
        self.assertEqual('MEX', airport.iata_code)
        self.assertEqual('America/Mexico_City', airport.timezone)
        self.assertEqual( 'low_cost', airport.viaticum)


class TestStr(TestAirport):
    def test___str__(self):
        self.assertEqual(self.airport.__str__(), "MEX")
