from unittest import TestCase

from model.scheduleClasses import Equipment


class TestEquipment(TestCase):

    def setUp(self):
        self.eq1 = Equipment()
        self.eq = Equipment(airplane_code="737", max_crew_members=4)


class TestInit(TestEquipment):

    def test_initial_values(self):
        self.assertIsNone(self.eq1.airplane_code)
        self.assertIsNone(self.eq1.max_crew_members)
        self.assertEqual(self.eq.airplane_code, '737')
        self.assertEqual(self.eq.max_crew_members, 4)


class TestStr(TestEquipment):

    def test_str_method(self):
        self.assertEqual(str(self.eq), '737')
        self.assertEqual(str(self.eq1), 3 * '')
