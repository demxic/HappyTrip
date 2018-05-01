import unittest
from model.scheduleClasses import Airport


class TestAirport(unittest.TestCase):
    def setUp(self):
        self.airport = Airport(iata_code='MEX', timezone='America/Mexico_City', viaticum=None)


class TestInit(TestAirport):
    def test_iata_code(self):
        self.assertEqual(self.airport.iata_code, 'MEX')

    def test_timezone(self):
        self.assertEqual(self.airport.timezone, 'America/Mexico_City')

    def test_viaticum(self):
        self.assertEqual(self.airport.viaticum, None)


class TestStr(TestAirport):
    def test___str__(self):
        self.assertEqual(self.airport.__str__(), "MEX")
