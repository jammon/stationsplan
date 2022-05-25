from django.conf import settings
from django_ical.views import ICalFeed
from django.db.models import F

from sp_app.models import Person, Planning


class DienstFeed(ICalFeed):
    """
    A simple event calender
    """

    product_id = "-//stationsplan.de//DE"
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
            .filter(start__lt=F("ward__approved"))
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
        return settings.DOMAIN + "/plan"
