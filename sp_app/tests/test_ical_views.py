from datetime import date
from django.core import mail
from django.urls import reverse
from icalendar import Calendar

from sp_app.models import Ward, Planning, FeedId
from sp_app.tests.utils_for_tests import PopulatedTestCase, LoggedInTestCase
from sp_app.logic import set_approved
from sp_app.ical_views import DienstFeed


class TestDienstFeed(PopulatedTestCase):
    """Test the ical feed"""

    def setUp(self):
        super().setUp()
        FeedId.objects.create(uid="abc", person=self.person_a)
        self.nightshift = Ward.objects.create(
            name="Nightshift",
            shortname="N",
            min=0,
            max=5,
            company=self.company,
            in_ical_feed=True,
        )

    def plan_shift(self, person, day):
        Planning.objects.create(
            company=self.company,
            person=person,
            ward=self.nightshift,
            start=day,
            end=day,
        )

    def test_feed(self):
        for person, day in (
            (self.person_a, date(2022, 5, 13)),
            (self.person_b, date(2022, 5, 14)),
            (self.person_a, date(2022, 5, 15)),
        ):
            self.plan_shift(person, day)
        response = self.client.get(reverse("icalfeed", args=["abc"]))
        cal = Calendar.from_ical(response.content)
        events = [comp for comp in cal.walk() if comp.name == "VEVENT"]
        assert len(events) == 2
        for ev in events:
            assert ev.get("summary") == "Nightshift"
        for ev, day in zip(events, ["2022-05-15", "2022-05-13"]):
            assert str(ev.decoded("dtstart")) == day
            assert str(ev.decoded("dtend")) == day

    def test_feed_items(self):
        for person, day in (
            (self.person_a, date(2022, 5, 13)),
            (self.person_a, date(2022, 6, 15)),
        ):
            self.plan_shift(person, day)
        self.nightshift.departments.add(self.department)
        set_approved(["N"], "20220601", [self.department.id])
        f = DienstFeed()
        plannings = f.items(self.person_a)
        assert len(plannings) == 1
        assert plannings[0].start == date(2022, 5, 13)


class TestMailFeed(LoggedInTestCase):
    """Test the mailing of the ical feed"""

    employee_level = "is_dep_lead"

    def test_send_ical_feed(self):
        url = reverse("send_ical_feed", args=[self.person_a.pk])
        response = self.client.get(url)
        assert len(mail.outbox) == 0
        assert response.content == b"<td>Mailadresse fehlt</td>"

        self.person_a.email = "mail@example.com"
        self.person_a.save()
        response = self.client.get(url)
        assert len(mail.outbox) == 1
        m = mail.outbox[0]
        assert m.subject == "Kalender für Person A"
        feedid = self.person_a.feed_ids.first()
        assert feedid.uid in m.body
