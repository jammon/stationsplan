# -*- coding: utf-8 -*-
from datetime import date, timedelta

from sp_app.models import (
    Person,
    Ward,
    ChangeLogging,
    Planning,
    process_change,
    FAR_FUTURE,
)
from sp_app.utils import PopulatedTestCase


class TestPerson(PopulatedTestCase):
    def test_person(self):
        person = Person.objects.create(
            name="Heinz Müller",
            shortname="Mül",
            start_date=date(2015, 1, 1),
            end_date=date(2015, 12, 31),
            company=self.company,
        )
        person.departments.add(self.department)
        self.assertEqual(
            person.toJson(),
            {
                "name": "Heinz Müller",
                "shortname": "Mül",
                "id": person.id,
                "start_date": [2015, 0, 1],
                "end_date": [2015, 11, 31],
                "functions": [],
                "departments": [self.department.id],
                "position": "01",
                "anonymous": False,
                "external": False,
            },
        )

    def test_persons_leave_terminates_planning(self):
        person = Person.objects.create(
            name="Heinz Müller",
            shortname="Mül",
            start_date=date(2015, 1, 1),
            company=self.company,
        )
        Planning.objects.create(
            person=person,
            ward=self.ward_a,
            start=date(2016, 6, 1),
            end=FAR_FUTURE,
        )
        Planning.objects.create(
            person=person,
            ward=self.ward_b,
            start=date(2016, 8, 1),
            end=date(2016, 8, 5),
        )
        person.end_date = date(2016, 6, 30)
        person.save()
        planning = Planning.objects.get(person=person, ward=self.ward_a)
        self.assertEqual(planning.end, date(2016, 6, 30))
        try:
            planning = Planning.objects.get(person=person, ward=self.ward_b)
            self.assertEqual(planning.start, date(2016, 8, 1))
            self.assertEqual(planning.end, date(2016, 8, 5))
        except Planning.DoesNotExist:
            self.fail(
                "Plannings of leaving persons that end (like vacations) "
                "should not be deleted in case they would change their "
                "minds"
            )

    def test_planning_does_not_exceed_persons_time(self):
        person = Person.objects.create(
            name="Heinz Müller",
            shortname="Mül",
            start_date=date(2015, 1, 1),
            end_date=date(2016, 6, 30),
            company=self.company,
        )
        planning = Planning.objects.create(
            person=person,
            ward=self.ward_a,
            start=date(2016, 6, 1),
            end=FAR_FUTURE,
        )
        self.assertEqual(planning.end, date(2016, 6, 30))


class TestWard(PopulatedTestCase):
    def test_ward(self):
        kwargs = {
            "min": 1,
            "max": 3,
            "company": self.company
        }
        ward = Ward.objects.create(
            name="Station A",
            shortname="A",
            # min=1,
            # max=3,
            everyday=False,
            freedays=False,
            on_leave=False,
            # company=self.company,
            position=2,
            **kwargs
        )
        ward_b = Ward.objects.create(
            name="Station B",
            shortname="B",
            **kwargs)
        ward_c = Ward.objects.create(
            name="Station C",
            shortname="C",
            **kwargs)
        ward.after_this.add(ward_b, ward_c)
        ward.not_with_this.add(ward_c)
        self.assertEqual(
            ward.toJson(),
            {
                "name": "Station A",
                "shortname": "A",
                "id": ward.id,
                "min": 1,
                "max": 3,
                "everyday": False,
                "freedays": False,
                "weekdays": "",
                "callshift": False,
                "on_leave": False,
                "company_id": self.company.id,
                "position": "02",
                "after_this": "B,C",
                "not_with_this": "C",
                "ward_type": "",
                "weight": 0,
                "active": True,
            },
        )
        ward.approved = date(2017, 3, 30)
        self.assertEqual(ward.toJson()["approved"], [2017, 2, 30])


class TestChanges(PopulatedTestCase):
    def test_change_logging(self):
        c = ChangeLogging(
            person=self.person_a,
            ward=self.ward_a,
            day=date(2015, 10, 2),
            added=True,
        )
        expected = {
            "person": self.person_a.shortname,
            "ward": self.ward_a.shortname,
            "day": "20151002",
            "continued": True,
            "action": "add",
        }
        self.assertContainsDict(c.toJson(), expected)
        c.added = False
        expected["action"] = "remove"
        self.assertContainsDict(c.toJson(), expected)

    def test_description(self):  # gehört nach test_models
        testdata = (
            (
                self.person_a,
                self.ward_a,
                date(2015, 9, 14),
                True,
                False,
                "Mr. User: Person A ist am 14.09.2015 für Ward A eingeteilt",
            ),
            (
                self.person_a,
                self.ward_a,
                date(2015, 10, 31),
                True,
                True,
                "Mr. User: Person A ist ab 31.10.2015 für Ward A eingeteilt",
            ),
            (
                self.person_b,
                self.ward_a,
                date(2015, 11, 6),
                False,
                True,
                "Mr. User: Person B ist ab 06.11.2015 nicht mehr für Ward A "
                "eingeteilt",
            ),
        )

        for (person, ward, day, added, continued, expected) in testdata:
            cl = ChangeLogging(
                person=person,
                ward=ward,
                day=day,
                added=added,
                continued=continued,
                company=self.company,
                user=self.user,
            )
            cl.make_description()
            self.assertEqual(cl.description, expected)
        cl = ChangeLogging(
            person=self.person_a,
            ward=self.ward_a,
            day=date(2015, 9, 14),
            added=True,
            until=date(2015, 9, 16),
            company=self.company,
            user=self.user,
        )
        cl.make_description()
        self.assertEqual(
            cl.description,
            "Mr. User: Person A ist von 14.09.2015 bis 16.09.2015 "
            "für Ward A eingeteilt",
        )


class Process_Change_Testcase(PopulatedTestCase):
    def _do_test(self, changes, expected_plannings):
        for c in changes:
            process_change(
                ChangeLogging.objects.create(
                    user_id=1,
                    person=self.person_a,
                    ward_id=1,
                    company=self.company,
                    **c
                )
            )
        plannings = Planning.objects.filter(
            superseded_by__isnull=True
        ).order_by("start")
        self.assertEqual(len(plannings), len(expected_plannings))
        for planning, expected in zip(plannings, expected_plannings):
            self.assertEqual(planning.start, expected["start"])
            self.assertEqual(planning.end, expected["end"])


date_07 = date(2016, 3, 7)
date_08 = date(2016, 3, 8)
date_09 = date(2016, 3, 9)
date_10 = date(2016, 3, 10)
date_11 = date(2016, 3, 11)
date_12 = date(2016, 3, 12)
date_14 = date(2016, 3, 14)
ONE_DAY = timedelta(1)


class Test_One_Change(Process_Change_Testcase):
    def test_add_continued(self):
        self._do_test(
            ({"day": date_10, "added": True, "continued": True},),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_add_oneday(self):
        self._do_test(
            ({"day": date_10, "added": True, "continued": False},),
            ({"start": date_10, "end": date_10},),
        )

    def test_remove_continued(self):
        self._do_test(
            ({"day": date_10, "added": False, "continued": True},), ()
        )

    def test_remove_oneday(self):
        self._do_test(
            ({"day": date_10, "added": False, "continued": False},), ()
        )


class Test_Two_Changes(Process_Change_Testcase):

    # two adds in sequence
    def test_two_adds_1a(self):
        """Two adds on the same day (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_10, "added": True, "continued": True},
            ),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_two_adds_1b(self):
        """Two adds on the same day (cont. then one day)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_10, "added": True, "continued": False},
            ),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_two_adds_1c(self):
        """Two adds on the same day (one day then cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": False},
                {"day": date_10, "added": True, "continued": True},
            ),
            ({"start": date_10, "end": date_10},),
        )

    def test_two_adds_2a(self):
        """Second add is after the first (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_11, "added": True, "continued": True},
            ),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_two_adds_2b(self):
        """Second add is after the first (cont. then one day)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_11, "added": True, "continued": False},
            ),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_two_adds_2c(self):
        """Second add is after the first (one day then cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": False},
                {"day": date_11, "added": True, "continued": True},
            ),
            (
                {"start": date_10, "end": date_10},
                {"start": date_11, "end": FAR_FUTURE},
            ),
        )

    def test_two_adds_3a(self):
        """Second add is before the first (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_08, "added": True, "continued": True},
            ),
            (
                {"start": date_08, "end": date_09},
                {"start": date_10, "end": FAR_FUTURE},
            ),
        )

    def test_two_adds_3b(self):
        """Second add is before the first (cont. then one day)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_08, "added": True, "continued": False},
            ),
            (
                {"start": date_08, "end": date_08},
                {"start": date_10, "end": FAR_FUTURE},
            ),
        )

    def test_two_adds_3c(self):
        """Second add is before the first (one day then cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": False},
                {"day": date_08, "added": True, "continued": True},
            ),
            (
                {"start": date_08, "end": date_09},
                {"start": date_10, "end": date_10},
            ),
        )

    # ---------------------------------------------------------------------

    # two removes in sequence
    # (since one remove alone produces no planning,
    # the same should hold for two)
    def test_two_removes_1a(self):
        """Two removes on the same day (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": True},
                {"day": date_10, "added": False, "continued": True},
            ),
            (),
        )

    def test_two_removes_1b(self):
        """Two removes on the same day (cont. then one day)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": True},
                {"day": date_10, "added": False, "continued": False},
            ),
            (),
        )

    def test_two_removes_1c(self):
        """Two removes on the same day (one day then cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": False},
                {"day": date_10, "added": False, "continued": True},
            ),
            (),
        )

    def test_two_removes_2a(self):
        """Second remove is after the first (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": True},
                {"day": date_11, "added": False, "continued": True},
            ),
            (),
        )

    def test_two_removes_2b(self):
        """Second remove is after the first (cont. then one day)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": True},
                {"day": date_11, "added": False, "continued": False},
            ),
            (),
        )

    def test_two_removes_2c(self):
        """Second remove is after the first (one day then cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": False},
                {"day": date_11, "added": False, "continued": True},
            ),
            (),
        )

    def test_two_removes_3a(self):
        """Second remove is before the first (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": True},
                {"day": date_08, "added": False, "continued": True},
            ),
            (),
        )

    def test_two_removes_3b(self):
        """Second remove is before the first (cont. then one day)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": True},
                {"day": date_08, "added": False, "continued": False},
            ),
            (),
        )

    def test_two_removes_3c(self):
        """Second remove is before the first (one day then cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": False, "continued": False},
                {"day": date_08, "added": False, "continued": True},
            ),
            (),
        )

    # ---------------------------------------------------------------------

    # add then remove in sequence
    def test_add_then_remove_1a(self):
        """Both on the same day (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_10, "added": False, "continued": True},
            ),
            (),
        )

    def test_add_then_remove_1b(self):
        """Both on the same day (add cont., remove one day)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_10, "added": False, "continued": False},
            ),
            ({"start": date_11, "end": FAR_FUTURE},),
        )

    def test_add_then_remove_1c(self):
        """Both on the same day (add one day, remove cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": False},
                {"day": date_10, "added": False, "continued": True},
            ),
            (),
        )

    def test_add_then_remove_2a(self):
        """Remove is after add (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_11, "added": False, "continued": True},
            ),
            ({"start": date_10, "end": date_10},),
        )

    def test_add_then_remove_2b(self):
        """Remove is after add (add cont., remove one day)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_11, "added": False, "continued": False},
            ),
            (
                {"start": date_10, "end": date_10},
                {"start": date_12, "end": FAR_FUTURE},
            ),
        )

    def test_add_then_remove_2c(self):
        """Remove is after add (add one day, remove cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": False},
                {"day": date_11, "added": False, "continued": True},
            ),
            ({"start": date_10, "end": date_10},),
        )

    def test_add_then_remove_3a(self):
        """Remove is before add (both cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_08, "added": False, "continued": True},
            ),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_add_then_remove_3b(self):
        """Remove is before add (add cont., remove one day)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_08, "added": False, "continued": False},
            ),
            ({"start": date_10, "end": FAR_FUTURE},),
        )

    def test_add_then_remove_3c(self):
        """Remove is before add (add one day, remove cont.)"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": False},
                {"day": date_08, "added": False, "continued": True},
            ),
            ({"start": date_10, "end": date_10},),
        )

    # ---------------------------------------------------------------------


class Test_Special_Cases(Process_Change_Testcase):
    def test_special_1(self):
        """Earlier plannings should not overshadow later ones"""
        self._do_test(
            (
                {"day": date_10, "added": True, "continued": True},
                {"day": date_12, "added": False, "continued": True},
                {"day": date_07, "added": True, "continued": True},
                {"day": date_08, "added": False, "continued": True},
            ),
            (
                {"start": date_07, "end": date_07},
                {"start": date_10, "end": date_11},
            ),
        )


add_cont = {"added": True, "continued": True}
rem_cont = {"added": False, "continued": True}


class Test_Changes_with_End(Process_Change_Testcase):
    def test_add_with_no_other_plannings(self):
        self._do_test(
            (dict(day=date_10, until=date_12, **add_cont),),
            (dict(start=date_10, end=date_12),),
        )

    def test_add_planning_covered_totally(self):
        self._do_test(
            (
                dict(day=date_10, until=date_12, **add_cont),
                dict(day=date_08, until=date_14, **add_cont),
            ),
            (dict(start=date_08, end=date_14),),
        )

    def test_add_planning_covered_partially(self):
        self._do_test(
            (
                dict(day=date_10, until=date_14, **add_cont),
                dict(day=date_08, until=date_12, **add_cont),
            ),
            (
                dict(start=date_08, end=date_10 - ONE_DAY),
                dict(start=date_10, end=date_14),
            ),
        )

    def test_rem_with_no_other_plannings(self):
        self._do_test((dict(day=date_10, until=date_12, **rem_cont),), ())

    def test_rem_planning_covered_totally(self):
        self._do_test(
            (
                dict(day=date_10, until=date_12, **add_cont),
                dict(day=date_08, until=date_14, **rem_cont),
            ),
            (),
        )

    def test_rem_planning_begin_covered_partially(self):
        self._do_test(
            (
                dict(day=date_10, until=date_14, **add_cont),
                dict(day=date_08, until=date_12, **rem_cont),
            ),
            (dict(start=date_12 + ONE_DAY, end=date_14),),
        )

    def test_rem_planning_end_covered_partially(self):
        self._do_test(
            (
                dict(day=date_08, until=date_12, **add_cont),
                dict(day=date_10, until=date_14, **rem_cont),
            ),
            (dict(start=date_08, end=date_10 - ONE_DAY),),
        )

    def test_rem_planning_combined(self):
        self._do_test(
            (
                dict(day=date_07, until=date_09, **add_cont),
                dict(day=date_10, until=date_11, **add_cont),
                dict(day=date_12, until=date_14, **add_cont),
                dict(day=date_09, until=date_12, **rem_cont),
            ),
            (
                dict(start=date_07, end=date_09 - ONE_DAY),
                dict(start=date_12 + ONE_DAY, end=date_14),
            ),
        )
