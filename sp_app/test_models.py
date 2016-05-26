# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import date

from .models import (Person, ChangeLogging, Planning, process_change,
                     FAR_FUTURE)
from .utils import PopulatedTestCase


class TestChanges(PopulatedTestCase):

    def test_person(self):
        person = Person.objects.create(name="Heinz Müller", shortname="Mül",
                                       start_date=date(2015, 1, 1),
                                       end_date=date(2015, 12, 31),
                                       company=self.company)
        self.assertEqual(person.toJson(),
                         {'name': "Heinz Müller",
                          'id': "Mül",
                          'start_date': [2015, 0, 1],
                          'end_date': [2015, 11, 31],
                          'functions': [],
                          'position': 1, })

    def test_change_logging(self):
        c = ChangeLogging(person=self.person_a, ward=self.ward_a,
                          day=date(2015, 10, 2),
                          added=True)
        expected = {'person': "A", 'ward': "A", 'day': "20151002",
                    'continued': True, 'action': "add", }
        self.assertEqual(c.toJson(), expected)
        c.added = False
        expected['action'] = "remove"
        self.assertEqual(c.toJson(), expected)

    def test_description(self):  # gehört nach test_models
        testdata = (
            (self.person_a, self.ward_a, date(2015, 9, 14), True, False,
             "Mr. User: Person A ist am 14.09.2015 für Ward A eingeteilt"),
            (self.person_a, self.ward_a, date(2015, 10, 31), True, True,
             "Mr. User: Person A ist ab 31.10.2015 für Ward A eingeteilt"),
            (self.person_b, self.ward_a, date(2015, 11, 6), False, True,
             "Mr. User: Person B ist ab 06.11.2015 nicht mehr für Ward A "
             "eingeteilt"))

        for (person, ward, day, added, continued, expected) in testdata:
            cl = ChangeLogging(
                person=person, ward=ward, day=day, added=added,
                continued=continued, company=self.company, user=self.user)
            cl.make_description()
            self.assertEqual(cl.description, expected)


class Process_Change_Testcase(PopulatedTestCase):

    def _do_test(self, changes, expected_plannings):
        for c in changes:
            process_change(ChangeLogging.objects.create(
                day=c['day'],
                added=c['added'],
                continued=c['continued'],
                user_id=1, person=self.person_a, ward_id=1,
                company=self.company))
        plannings = Planning.objects.all().order_by('start')
        self.assertEqual(len(plannings), len(expected_plannings))
        for planning, expected in zip(plannings, expected_plannings):
            self.assertEqual(planning.start, expected['start'])
            self.assertEqual(planning.end, expected['end'])


class Test_One_Change(Process_Change_Testcase):

    def test_add_continued(self):
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_add_oneday(self):
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},))

    def test_remove_continued(self):
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},),
            ())

    def test_remove_oneday(self):
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': False},),
            ())


class Test_Two_Changes(Process_Change_Testcase):

    # two adds in sequence
    def test_two_adds_1a(self):
        """ Two adds on the same day (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 8), 'added': True, 'continued': True}, ),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_two_adds_1b(self):
        """ Two adds on the same day (cont. then one day) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 8), 'added': True, 'continued': False}, ),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_two_adds_1c(self):
        """ Two adds on the same day (one day then cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},
             {'day': date(2016, 3, 8), 'added': True, 'continued': True}, ),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},))

    def test_two_adds_2a(self):
        """ Second add is after the first (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 9), 'added': True, 'continued': True},),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_two_adds_2b(self):
        """ Second add is after the first (cont. then one day)"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 9), 'added': True, 'continued': False},),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_two_adds_2c(self):
        """ Second add is after the first (one day then cont.)"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},
             {'day': date(2016, 3, 9), 'added': True, 'continued': True},),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},
             {'start': date(2016, 3, 9), 'end': FAR_FUTURE},))

    def test_two_adds_3a(self):
        """ Second add is before the first (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 6), 'added': True, 'continued': True},),
            ({'start': date(2016, 3, 6), 'end': date(2016, 3, 7)},
             {'start': date(2016, 3, 8), 'end': FAR_FUTURE}, ))

    def test_two_adds_3b(self):
        """ Second add is before the first (cont. then one day) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 6), 'added': True, 'continued': False},),
            ({'start': date(2016, 3, 6), 'end': date(2016, 3, 6)},
             {'start': date(2016, 3, 8), 'end': FAR_FUTURE}, ))

    def test_two_adds_3c(self):
        """ Second add is before the first (one day then cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},
             {'day': date(2016, 3, 6), 'added': True, 'continued': True},),
            ({'start': date(2016, 3, 6), 'end': date(2016, 3, 7)},
             {'start': date(2016, 3, 8), 'end': date(2016, 3, 8)}, ))
    # ---------------------------------------------------------------------

    # two removes in sequence
    # (since one remove alone produces no planning,
    # the same should hold for two)
    def test_two_removes_1a(self):
        """ Two removes on the same day (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},
             {'day': date(2016, 3, 8), 'added': False, 'continued': True},),
            ())

    def test_two_removes_1b(self):
        """ Two removes on the same day (cont. then one day) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},
             {'day': date(2016, 3, 8), 'added': False, 'continued': False},),
            ())

    def test_two_removes_1c(self):
        """ Two removes on the same day (one day then cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': False},
             {'day': date(2016, 3, 8), 'added': False, 'continued': True},),
            ())

    def test_two_removes_2a(self):
        """ Second remove is after the first (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},
             {'day': date(2016, 3, 9), 'added': False, 'continued': True},),
            ())

    def test_two_removes_2b(self):
        """ Second remove is after the first (cont. then one day)"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},
             {'day': date(2016, 3, 9), 'added': False, 'continued': False},),
            ())

    def test_two_removes_2c(self):
        """ Second remove is after the first (one day then cont.)"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': False},
             {'day': date(2016, 3, 9), 'added': False, 'continued': True},),
            ())

    def test_two_removes_3a(self):
        """ Second remove is before the first (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},
             {'day': date(2016, 3, 6), 'added': False, 'continued': True},),
            ())

    def test_two_removes_3b(self):
        """ Second remove is before the first (cont. then one day) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': True},
             {'day': date(2016, 3, 6), 'added': False, 'continued': False},),
            ())

    def test_two_removes_3c(self):
        """ Second remove is before the first (one day then cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': False, 'continued': False},
             {'day': date(2016, 3, 6), 'added': False, 'continued': True},),
            ())
    # ---------------------------------------------------------------------

    # add then remove in sequence
    def test_add_then_remove_1a(self):
        """ Both on the same day (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 8), 'added': False, 'continued': True}, ),
            ())

    def test_add_then_remove_1b(self):
        """ Both on the same day (add cont., remove one day) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 8), 'added': False, 'continued': False}, ),
            ({'start': date(2016, 3, 9), 'end': FAR_FUTURE},))

    def test_add_then_remove_1c(self):
        """ Both on the same day (add one day, remove cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},
             {'day': date(2016, 3, 8), 'added': False, 'continued': True}, ),
            ())

    def test_add_then_remove_2a(self):
        """ Remove is after add (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 9), 'added': False, 'continued': True}, ),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},))

    def test_add_then_remove_2b(self):
        """ Remove is after add (add cont., remove one day)"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 9), 'added': False, 'continued': False}, ),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},
             {'start': date(2016, 3, 10), 'end': FAR_FUTURE},))

    def test_add_then_remove_2c(self):
        """ Remove is after add (add one day, remove cont.)"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},
             {'day': date(2016, 3, 9), 'added': False, 'continued': True}, ),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},))

    def test_add_then_remove_3a(self):
        """ Remove is before add (both cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 6), 'added': False, 'continued': True}, ),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_add_then_remove_3b(self):
        """ Remove is before add (add cont., remove one day) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 6), 'added': False, 'continued': False}, ),
            ({'start': date(2016, 3, 8), 'end': FAR_FUTURE},))

    def test_add_then_remove_3c(self):
        """ Remove is before add (add one day, remove cont.) """
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': False},
             {'day': date(2016, 3, 6), 'added': False, 'continued': True}, ),
            ({'start': date(2016, 3, 8), 'end': date(2016, 3, 8)},))
    # ---------------------------------------------------------------------


class Test_Special_Cases(Process_Change_Testcase):

    def test_special_1(self):
        """ Earlier plannings should not overshadow later ones"""
        self._do_test(
            ({'day': date(2016, 3, 8), 'added': True, 'continued': True},
             {'day': date(2016, 3, 10), 'added': False, 'continued': True},
             {'day': date(2016, 3, 5), 'added': True, 'continued': True},
             {'day': date(2016, 3, 6), 'added': False, 'continued': True}, ),
            ({'start': date(2016, 3, 5), 'end': date(2016, 3, 5)},
             {'start': date(2016, 3, 8), 'end': date(2016, 3, 9)}, ))
