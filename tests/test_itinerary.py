from datetime import datetime, timedelta
from unittest import TestCase

from model.scheduleClasses import Itinerary
from model.timeClasses import Duration


class TestItinerary(TestCase):

    def setUp(self):
        # Itinerary 1  14:30 - 18:17  (3:47)
        self.begin1 = datetime(2018, 4, 28, 14, 30)
        self.end1 = datetime(2018, 4, 28, 18, 17)
        self.td1 = timedelta(hours=3, minutes=47)
        self.i1 = Itinerary(self.begin1, self.end1)

        # Itinerary 2  23:30 - 02:12   (2:42)
        self.begin2 = datetime(2018, 4, 28, 23, 30)
        self.end2 = datetime(2018, 4, 29, 2, 12)
        self.td2 = timedelta(hours=2, minutes=42)
        self.i2 = Itinerary.from_timedelta(self.begin2, self.td2)


class TestInit(TestItinerary):
    def test_initial_begin(self):
        self.assertEqual(self.begin1, self.i1.begin)

    def test_initial_end(self):
        self.assertEqual(self.end1, self.i1.end)


class TestFromTimeDelta(TestItinerary):
    def test_initial_begin(self):
        self.assertEqual(self.begin2, self.i2.begin)

    def test_initial_end(self):
        self.assertEqual(self.end2, self.i2.end)


class TestDuration(TestItinerary):
    def test_duration(self):
        d = Duration.from_timedelta(self.end1 - self.begin1)
        self.assertEqual(d.minutes, self.i1.duration.minutes)


class TestElapsedDates(TestItinerary):
    pass


class TestOverlaps(TestItinerary):
    pass


class TestStr(TestItinerary):
    def test_string(self):
        self.assertEqual('28Apr BEGIN 1430 END 1817', self.i1.__str__())


