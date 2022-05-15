from datetime import date
from django.test import Client
from django.urls import reverse
from icalendar import Calendar

from sp_app.models import Ward, Planning, FeedId
from sp_app.utils import PopulatedTestCase


class TestDienstFeed(PopulatedTestCase):
    """Test the ical feed"""

    def setUp(self):
        super().setUp()
        FeedId.objects.create(uid="abc", person=self.person_a)
        nightshift = Ward.objects.create(
            name="Nightshift",
            shortname="N",
            min=0,
            max=5,
            company=self.company,
            in_ical_feed=True,
        )
        for person, day in (
            (self.person_a, date(2022, 5, 13)),
            (self.person_b, date(2022, 5, 14)),
            (self.person_a, date(2022, 5, 15)),
        ):
            Planning.objects.create(
                company=self.company,
                person=person,
                ward=nightshift,
                start=day,
                end=day,
            )

    def test_feed(self):
        c = Client()
        response = c.get(reverse("icalfeed", args=["abc"]))
        cal = Calendar.from_ical(response.content)
        events = [comp for comp in cal.walk() if comp.name == "VEVENT"]
        assert len(events) == 2
        for ev in events:
            assert ev.get("summary") == "Nightshift"
        for ev, day in zip(events, ["2022-05-15", "2022-05-13"]):
            assert str(ev.decoded("dtstart")) == day
            assert str(ev.decoded("dtend")) == day
