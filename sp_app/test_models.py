from datetime import date

from .models import Person, ChangingStaff
from .utils import PopulatedTestCase


class Test_ToJson(PopulatedTestCase):

    def setUp(self):
        super(Test_ToJson, self).setUp()
        self.person = Person(
            name="Heinz Müller", shortname="Mül", start_date=date(2015, 1, 1),
            end_date=date(2015, 12, 31), department=self.department,
            company=self.company)

    def test_person(self):
        self.assertEqual(self.person.toJson(),
                         {'name': "Heinz Müller",
                          'id': "Mül",
                          'start_date': [2015, 0, 1],
                          'end_date': [2015, 11, 31], })

    def test_to_json(self):
        c = ChangingStaff(
            person=self.person, ward=self.ward_a, day=date(2015, 10, 2),
            added=True)
        expected = {'person': "Mül", 'ward': "A", 'day': "20151002",
                    'action': "add", }
        self.assertEqual(c.toJson(), expected)
        c.added = False
        expected['action'] = "remove"
        self.assertEqual(c.toJson(), expected)
