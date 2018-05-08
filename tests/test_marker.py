import datetime
from unittest import TestCase

from model.scheduleClasses import Marker, Itinerary


class TestMarker(TestCase):

    def setUp(self):
        self.begin = datetime.datetime(2018, 5, 1, 0, 1)
        self.end = datetime.datetime(2018, 5, 1, 23, 59)
        self.it1 = Itinerary(begin=self.begin, end=self.end)
        self.marker = Marker('X', self.it1, None)


class TestInit(TestMarker):

    def test_initial_values(self):
        self.assertIsNotNone(self.marker.name)
        self.assertIsNone(self.marker.actual_itinerary)
        self.assertIsNotNone(self.marker.scheduled_itinerary)


class TestBegin(TestMarker):

    def test_begin_datetime(self):
        print(self.marker)
        self.assertEqual(self.marker.begin, self.begin)


class TestEnd(TestMarker):

    def test_end_datetime(self):
        self.assertEqual(self.marker.end, self.end)


class TestReport(TestMarker):

    def test_report(self):
        self.assertEqual(self.marker.report, self.marker.begin)


class TestStr(TestMarker):

    def test_str_method(self):
        marker_string = str(self.marker)
        self.assertEqual("X 01May BEGIN 0001 END 2359", marker_string)