from datetime import date, timedelta
from django_ical.views import ICalFeed
from sp_app.models import Person, Planning

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

    def title(self, obj):
        return f"Dienste für {obj.name}"

    def file_name(self, obj):
        return f"dienste_{obj.name}.ics"

    def get_object(self, request, feed_id):
        person = Person.objects.get(
            feed_ids__uid=feed_id, feed_ids__active=True
        )
        person.inactivate_older_feeds(feed_id)
        person.current_feedid = feed_id
        return person

    def items(self, person):
        return (
            Planning.objects.filter(
                person=person,
                start__lt=person.end_date,
                ward__in_ical_feed=True,
            )
            .order_by("-start")
            .select_related("ward")
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
