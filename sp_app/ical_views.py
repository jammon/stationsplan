from datetime import date, timedelta
from django_ical.views import ICalFeed
from icalendar import Calendar, Event
from sp_app.models import Person, Planning, FeedId

CALENDAR_START = date(2021, 11, 1)
ONE_DAY = timedelta(days=1)
CAL_PRODID = "Stationsplan.de"
CAL_VERSION = "0.9"


class DienstFeed(ICalFeed):
    """
    A simple event calender
    """

    product_id = "-//stationsplan.de//TESTING//DE"
    timezone = "UTC"
    file_name = "dienste.ics"

    def get_object(self, request, feed_id):
        feed = FeedId.objects.get(uid=feed_id, active=True).select_related(
            "person"
        )
        feed.person.inactivate_older_feeds(feed)
        return feed.person

    def items(self, person):
        return (
            Planning.objects.filter(
                person=person,
                start__lt=person.end_date,
                ward__in_ical_feed=True,
            )
            .order_by("-start")
            .select_related("ward")[:3]
        )

    def item_title(self, planning):
        return planning.ward.name

    def item_description(self, planning):
        return planning.ward.name

    def item_start_datetime(self, planning):
        return planning.start

    def item_end_datetime(self, planning):
        return planning.end

    def item_link(self, planning):
        return "http://localhost:8000/plan"


def get_person_plannings(person_id, company_id):
    MAX_PLANNED_DAYS = 20

    cal = Calendar()
    cal.add("prodid", CAL_PRODID)
    cal.add("version", CAL_VERSION)

    plannings = Planning.objects.filter(
        person_id=person_id, company_id=company_id, start_gte=CALENDAR_START
    )
    for planning in plannings:
        dt_start, nr = planning.start, 0
        while dt_start <= planning.end and nr < MAX_PLANNED_DAYS:
            event = Event()
            event.add("dt_start", dt_start)
