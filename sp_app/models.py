# -*- coding: utf-8 -*-
import json
import string
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.utils.translation import gettext as _

from stationsplan.utils import random_string
from sp_app import utils

FAR_FUTURE = date(2099, 12, 31)
ONE_DAY = timedelta(days=1)


def date_to_json(date):
    return [date.year, date.month - 1, date.day]


class Company(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=50,
        help_text='Name der Klinik (z.B. "Waldklinik Neustadt")',
    )
    shortname = models.CharField(
        _("Short Name"),
        max_length=10,
        help_text='Abkürzung für die Klinik (z.B. "wkns")',
    )
    region = models.ForeignKey(
        "Region",
        null=True,
        blank=True,
        related_name="companies",
        help_text=_(
            "Region that determines the legal holidays for this company"
        ),
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    def __str__(self):
        return self.name


class UniqueField:
    def unique_error_message(self, model_class, unique_check):
        if model_class == type(self) and len(unique_check) == 2:
            for field, field_name in self.unique_fields:
                if unique_check == (field, "company"):
                    return f'Der {field_name} "{getattr(self, field)}" ist bereits vergeben und darf nicht doppelt vorkommen.'
        return super().unique_error_message(model_class, unique_check)


class Department(models.Model):
    name = models.CharField(_("Name"), max_length=50)
    shortname = models.CharField(
        _("Short Name"), max_length=10, null=True, blank=True
    )
    company = models.ForeignKey(
        Company,
        related_name="departments",
        help_text=_("The top organizational unit"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def __str__(self):
        if self.shortname:
            return f"{self.name} ({self.shortname})"
        return self.name


class Ward(UniqueField, models.Model):
    name = models.CharField(_("Name"), max_length=50)
    shortname = models.CharField(_("Short Name"), max_length=10)
    max = models.IntegerField(help_text=_("maximum staffing"))
    min = models.IntegerField(help_text=_("minimum staffing"))
    everyday = models.BooleanField(
        _("everyday"),
        default=False,
        help_text=_("if True, is to be planned also on free days."),
    )
    freedays = models.BooleanField(
        _("freedays"),
        default=False,
        help_text=_("if True, is to be planned only on free days."),
    )
    weekdays = models.CharField(
        _("weekdays"),
        max_length=7,
        default="",
        blank=True,
        help_text=_(
            "Days of the week when this is to be planned. "
            "(String of digits, 0  for sunday.)"
        ),
    )
    on_different_days = models.BooleanField(
        _("on_different_days"),
        default=False,
        help_text=_("This function can be planned on different days"),
    )
    callshift = models.BooleanField(
        _("callshift"),
        default=False,
        help_text=_("if True, then this function is displayed as call shift"),
    )
    on_leave = models.BooleanField(
        _("on_leave"),
        default=False,
        help_text=_("if True, then persons planned for this are on leave"),
    )
    departments = models.ManyToManyField(
        Department,
        verbose_name=_("Departments"),
        related_name="wards",
        help_text=_("Departments whose schedule contains this ward"),
    )
    company = models.ForeignKey(
        Company, related_name="wards", on_delete=models.CASCADE
    )
    position = models.IntegerField(
        default=1,
        help_text=_(
            "Ordering in the display. Should not be more than two digits."
        ),
    )
    ward_type = models.CharField(
        _("Ward type"),
        max_length=50,
        blank=True,
        default="",
        help_text=_("For sorting the CallTallies"),
    )
    approved = models.DateField(
        default=FAR_FUTURE,
        null=True,
        blank=True,
        help_text=_("The date until which the plan is approved"),
    )
    after_this = models.ManyToManyField(
        "self",
        verbose_name=_("after this"),
        symmetrical=False,
        blank=True,
        help_text=_(
            "if not empty, "
            "only these functions can be planned on the next day"
        ),
        related_name="predecessor",
    )
    not_with_this = models.ManyToManyField(
        "self",
        verbose_name=_("not with this"),
        symmetrical=False,
        blank=True,
        help_text=_("these functions can not be planned on the same day"),
        related_name="shadowing",
    )
    weight = models.IntegerField(
        default=0,
        help_text=_(
            "if this is a call shift, the weight reflects its "
            "burden on the persons doing the shift"
        ),
    )
    active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("This function should currently be displayed"),
    )
    in_ical_feed = models.BooleanField(
        _("Part of ical feed"),
        default=False,
        help_text=_("This function should be part of the ical feed"),
    )
    unique_fields = (("name", "Name"), ("shortname", "Kurzname"))

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["position", "name"]
        unique_together = [["name", "company"], ["shortname", "company"]]

    def __str__(self):
        return self.name

    def toJson(self):
        res = {
            "name": self.name,
            "shortname": self.shortname,
            "id": self.id,
            "min": self.min,
            "max": self.max,
            "everyday": self.everyday,
            "freedays": self.freedays,
            "weekdays": self.weekdays,
            "on_different_days": self.on_different_days,
            "callshift": self.callshift,
            "on_leave": self.on_leave,
            "company_id": self.company_id,
            "position": "%02d" % self.position,
            "after_this": "",
            "not_with_this": "",
            "ward_type": self.ward_type,
            "weight": self.weight,
            "active": self.active,
        }
        if self.pk:
            res["after_this"] = ",".join(
                w.shortname for w in self.after_this.all()
            )
            res["not_with_this"] = ",".join(
                w.shortname for w in self.not_with_this.all()
            )
        if self.approved < FAR_FUTURE:
            res["approved"] = date_to_json(self.approved)
        return res

    def clean(self):
        if self.shortname == "id":
            raise ValidationError(
                {"shortname": _('Wards cannot have the shortname "id".')}
            )
        if "," in self.shortname:
            raise ValidationError(
                {
                    "shortname": _(
                        "Wards cannot have a comma in their shortname."
                    )
                }
            )


class DifferentDay(models.Model):
    """A ward can be planned or not planned out of schedule"""

    day = models.DateField(_("day"), help_text=_("Day that is different"))
    ward = models.ForeignKey(
        Ward, related_name="different_days", on_delete=models.CASCADE
    )
    added = models.BooleanField(
        _("additional"), help_text=_("Planning is additional (not cancelled)")
    )

    class Meta:
        verbose_name = _("Different Day")
        verbose_name_plural = _("Different Days")


class Person(UniqueField, models.Model):
    """A person (worker) who can be planned for work"""

    POSITION_ASSISTENTEN = 1
    POSITION_OBERAERZTE = 2
    POSITION_CHEFAERZTE = 80
    POSITION_ANONYM = 4
    POSITION_EXTERNE = 5
    POSITION_CHOICES = (
        (POSITION_ASSISTENTEN, "Assistenten"),
        (POSITION_OBERAERZTE, "Oberärzte"),
        (POSITION_CHEFAERZTE, "Chefärzte"),
        (POSITION_ANONYM, "Anonym (Abteilung)"),
        (POSITION_EXTERNE, "Externe"),
    )

    name = models.CharField(_("Name"), max_length=50)
    shortname = models.CharField(_("Short Name"), max_length=10)
    start_date = models.DateField(
        _("start date"),
        default=utils.get_first_of_month,
        help_text=_("begin of job"),
    )
    end_date = models.DateField(
        _("end date"), default=FAR_FUTURE, help_text=_("end of job")
    )
    departments = models.ManyToManyField(
        Department, verbose_name=_("Departments"), related_name="persons"
    )
    company = models.ForeignKey(
        Company, related_name="persons", null=True, on_delete=models.CASCADE
    )
    functions = models.ManyToManyField(
        Ward,
        related_name="staff",
        verbose_name=_("Tasks"),
        help_text=_("Functions that he or she can  perform."),
    )
    position = models.IntegerField(
        _("position"),
        default=POSITION_ASSISTENTEN,
        choices=POSITION_CHOICES,
        help_text=_(
            "Ordering in the display. "
            "Should not be more than two digits. "
            "A number greater than 80 means Head of Department"
        ),
    )
    anonymous = models.BooleanField(
        _("Anonymous"),
        default=False,
        help_text=_(
            "if True this person represents multiple other persons, "
            "e.g. a department"
        ),
    )
    email = models.EmailField(_("Email"), null=True, blank=True)
    unique_fields = (("name", "Name"), ("shortname", "Kurzname"))

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")
        unique_together = [["name", "company"], ["shortname", "company"]]

    def __str__(self):
        return f"{self.name} ({self.shortname})"

    def toJson(self):
        return {
            "name": self.name,
            "shortname": self.shortname,
            "id": self.id,
            "start_date": date_to_json(self.start_date),
            "end_date": date_to_json(self.end_date),
            "functions": [f.shortname for f in self.functions.all()],
            "departments": [d.id for d in self.departments.all()],
            "position": "%02d" % self.position,
            "anonymous": self.anonymous,
            "external": self.position == Person.POSITION_EXTERNE,
        }

    def save(self, *args, **kwargs):
        created = not self.pk
        if created and self.position == Person.POSITION_ANONYM:
            self.anonymous = True
        super(Person, self).save(*args, **kwargs)
        # When a person leaves, their plannings should stop.
        # Plannings with an end (like vacations) are left untouched
        # in case the person changes their mind
        if self.end_date < FAR_FUTURE:
            Planning.objects.filter(
                person=self, start__gt=self.end_date, end=FAR_FUTURE
            ).delete()
            Planning.objects.filter(person=self, end=FAR_FUTURE).update(
                end=self.end_date
            )
        # every person can be on leave
        if created and not self.anonymous:
            self.functions.add(
                *list(
                    Ward.objects.filter(
                        company_id=self.company_id, on_leave=True
                    )
                )
            )

    def current(self):
        return self.end_date >= date.today()

    def inactivate_older_feeds(self, feed_id):
        feedids = list(FeedId.objects.filter(person=self, active=True))
        if len(feedids) < 2:
            return
        current_feed = next(f for f in feedids if f.uid == feed_id)
        older = []
        for f in feedids:
            if f.pk < current_feed.pk:
                f.active = False
                older.append(f)
        if older:
            FeedId.objects.bulk_update(older, ["active"])


class ChangeLogging(models.Model):
    """Logs who has made which changes.
    The change can be for one day (continued==False) or continued
    If continued==True it can have an end date (`until`)
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    day = models.DateField()
    added = models.BooleanField()
    continued = models.BooleanField(
        default=True, help_text="If False the change is valid for one day."
    )
    until = models.DateField(
        null=True,
        blank=True,
        help_text="The last day the change is valid. Can be blank.",
    )
    description = models.CharField(max_length=255)
    json = models.CharField(max_length=255)
    change_time = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0)
    current_version = 1

    class Meta:
        verbose_name = _("ChangeLogging")
        verbose_name_plural = _("ChangeLoggings")

    def toJson(self):
        data = {
            "person": self.person.shortname,
            "ward": self.ward.shortname,
            "day": self.day.strftime("%Y%m%d"),
            "action": "add" if self.added else "remove",
            "continued": self.continued,
            "pk": self.pk,
        }
        if self.until:
            data["until"] = self.until.strftime("%Y%m%d")
        return data

    def get_json_for_history(self):
        return {
            "user": self.user.get_full_name() or self.user.get_username(),
            "person": self.person.shortname,
            "ward": self.ward.shortname,
            "day": self.day,
            "added": self.added,
            "continued": self.continued,
            "until": self.until,
            "change_time": self.change_time,
        }

    def save(self, *args, **kwargs):
        self.make_description()
        self.version = self.current_version
        super(ChangeLogging, self).save(*args, **kwargs)
        # self.json contains the primary key
        self.json = json.dumps(self.toJson())
        ChangeLogging.objects.filter(pk=self.pk).update(json=self.json)

    def make_description(self):
        day = self.day.strftime("%d.%m.%Y")
        if not self.continued or (self.until and self.until == self.day):
            # am 19.11.2019
            time = f"am {day}"
        elif self.until:
            # von 19.11.2019 bis 20.11.2019
            time = f"von {day} bis {self.until.strftime('%d.%m.%Y')}"
        else:
            # ab 19.11.2019
            time = f"ab {day}"
        self.description = (
            f"{self.user.last_name or self.user.get_username()}: "
            f"{self.person.name} ist {time} "
            f'{"" if self.added else "nicht mehr "}für {self.ward.name}'
            f" eingeteilt"
        )

    def __str__(self):
        return self.description


def process_change(cl):
    """Weave the change into the existing Plannings.

    Return the json dict of the effective change to be returned to the client.
    """
    plannings = Planning.objects.filter(
        person_id=cl.person_id, ward_id=cl.ward_id
    )
    pl_data = dict(person_id=cl.person_id, ward_id=cl.ward_id)
    if cl.added:
        if cl.continued:
            end = cl.until or FAR_FUTURE
            plannings = list(
                plannings.filter(
                    end__gte=cl.day,
                    start__lte=end,
                ).order_by("start")
            )
            if len(plannings):
                # if cl.until is given and is before the end of the last
                #   overlapping planning
                # else it ends with the first planning in this period
                if cl.until:
                    last_planning = plannings[-1]
                    if cl.until < last_planning.end:
                        end = cl.until = last_planning.start - ONE_DAY
                        cl.save()
                        plannings.pop()
                else:
                    end = plannings[0].start - ONE_DAY
                if cl.day > end:  # This can happen if cl.until==None and
                    return {}  # change is in an existing planning
            pl = Planning.objects.create(start=cl.day, end=end, **pl_data)
            if cl.until and len(plannings) > 0:
                Planning.objects.filter(
                    id__in=[_pl.id for _pl in plannings]
                ).update(superseded_by=pl)
        else:  # not continued, one day
            plannings = plannings.filter(start__lte=cl.day, end__gte=cl.day)
            if len(plannings) == 0:
                Planning.objects.create(start=cl.day, end=cl.day, **pl_data)
            else:
                return {}  # change is contained in a Planning

    else:  # removed
        plannings = plannings.filter(
            start__lte=cl.until or cl.day, end__gte=cl.day
        ).order_by("start")
        if len(plannings) == 0:
            return {}
        if cl.continued:
            if cl.until:
                for pl in plannings:
                    if pl.start < cl.day:
                        if pl.end > cl.until:
                            Planning.objects.create(
                                start=cl.until + ONE_DAY, end=pl.end, **pl_data
                            )
                        pl.end = cl.day - ONE_DAY
                        pl.save()
                    elif pl.end > cl.until:
                        pl.start = cl.until + ONE_DAY
                        pl.save()
                    else:
                        pl.delete()  # cave: no undo!!
            else:
                for pl in plannings:  # should be only one planning
                    if pl.start == cl.day:
                        pl.delete()
                    else:
                        pl.end = cl.day - ONE_DAY
                        pl.save()
        else:  # not continued, one day
            for pl in plannings:
                if pl.start == pl.end:  # pl is one day
                    pl.delete()
                elif pl.start == cl.day:  # cut off first day
                    pl.start = cl.day + ONE_DAY
                    pl.save()
                else:
                    if not pl.end == cl.day:
                        Planning.objects.create(
                            start=cl.day + ONE_DAY, end=pl.end, **pl_data
                        )
                    pl.end = cl.day - ONE_DAY
                    pl.save()

    return json.loads(cl.json)


class Planning(models.Model):
    """One time period, where one person is planned for one ward.

    Plannings for the same person and ward should not overlap.
    The time period includes 'start' and 'end',
    i.e. a planning for one day has 'start' and 'end' set to the same date.
    """

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField(default=FAR_FUTURE)
    json = models.CharField(max_length=255)
    version = models.IntegerField(default=0)
    current_version = 1
    superseded_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="supersedes",
        default=None,
        help_text=_("Later planning that supersedes this one"),
    )
    updateddate = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Planning")
        verbose_name_plural = _("Plannings")

    def toJson(self):
        return {
            "person": self.person_id,
            "ward": self.ward_id,
            "start": self.start.strftime("%Y%m%d"),
            "end": self.end.strftime("%Y%m%d"),
        }

    def save(self, *args, **kwargs):
        if not self.pk:
            self.company_id = self.person.company_id
        self.json = json.dumps(self.toJson())
        self.version = self.current_version
        # the planning should not exceed the persons stay
        self.end = min(self.end, self.person.end_date)
        super(Planning, self).save(*args, **kwargs)

    def __str__(self):
        if self.end == FAR_FUTURE:
            return (
                f"{self.person.name} ist ab {self.start:%d.%m.%Y} "
                f"für {self.ward.name} geplant."
            )
        return (
            f"{self.person.name} ist von {self.start:%d.%m.%Y} bis "
            f"{self.end:%d.%m.%Y} für {self.ward.name} geplant."
        )


EMPLOYEE_PERMISSIONS = [
    ("is_company_admin", "is admin of the company"),
    ("is_dep_lead", "is leader of a department"),
    ("is_editor", "is editor for a department"),
]
EMPLOYEE_LEVEL = {
    "is_company_admin": "Admin",
    "is_dep_lead": "Abteilungsleiter/in",
    "is_editor": "Planen",
    "None": "Lesen",
}
EMPLOYEE_GROUP = {
    "is_company_admin": "Company Admin",
    "is_dep_lead": "Department admins",
    "is_editor": "Editors",
}


class Employee(models.Model):
    """Somebody who uses the plan.
    Can be anyone who works there, but also other involved personnel,
    like management etc.
    """

    user = models.OneToOneField(
        User, related_name="employee", on_delete=models.CASCADE
    )
    departments = models.ManyToManyField(
        Department, related_name="employees", verbose_name=_("Department")
    )
    company = models.ForeignKey(
        Company, related_name="employees", on_delete=models.CASCADE
    )
    _level = models.CharField("level", max_length=20, null=True)

    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        permissions = EMPLOYEE_PERMISSIONS

    def __str__(self):
        return "; ".join(
            (
                self.user.get_full_name() or self.user.get_username(),
                ", ".join([d.name for d in self.departments.all()]),
                self.company.name,
            )
        )

    def get_name(self):
        return self.user.get_full_name() or self.user.get_username()

    name = property(fget=get_name)

    def get_level(self):
        """Return level of authorization"""
        return self._level

    def set_level(self, level=None):
        """Set level of authorization

        If level is None or "None", remove all special permissions
        """
        assert level in EMPLOYEE_LEVEL or level in (None, "None")
        groups = dict((g.name, g) for g in Group.objects.all())
        self.user.groups.remove(
            *(groups[name] for name in EMPLOYEE_GROUP.values())
        )
        if level not in (None, "None"):
            # set all permissions up to the given level
            level_found = False
            for permission, docstring in EMPLOYEE_PERMISSIONS:
                if permission == level:
                    level_found = True
                if level_found:
                    self.user.groups.add(groups[EMPLOYEE_GROUP[permission]])
        # account for permission caching
        self.user = User.objects.get(id=self.user.id)
        self._level = None if level == "None" else level
        self.save()

    level = property(fget=get_level, fset=set_level)

    def name_and_level(self):
        # level = self.get_level()
        # if level is None:
        #     return self.name
        return f"{self.name} ({EMPLOYEE_LEVEL[self.level or 'None']})"


class StatusEntry(models.Model):
    """Saves some detail about the current status of the planning
    or the program

    Currently is only for setting the approved date of wards
    """

    name = models.CharField(max_length=30)
    content = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department,
        related_name="status_entries",
        null=True,
        blank=True,
        help_text=_("Can be empty"),
        on_delete=models.SET_NULL,
    )
    company = models.ForeignKey(
        Company,
        related_name="status_entries",
        null=True,
        blank=True,
        help_text=_("Can be empty"),
        on_delete=models.SET_NULL,
    )
    timestamp = models.DateTimeField(null=True, auto_now_add=True)

    def __str__(self):
        return f"{self.name}: {self.content}"


class CalculatedHoliday(models.Model):
    """A Holiday with calculated dates

    If mode is 'abs', the holiday is on that day and month,
    if year is not None, it is on that specific date.

    If mode is 'rel', then the holiday is 'day' days before or after easter.
    """

    name = models.CharField(_("Name"), max_length=50)
    mode = models.CharField(
        _("Mode"),
        max_length=3,
        choices=(("abs", _("Absolute")), ("rel", _("Easter-related"))),
    )
    day = models.IntegerField(
        _("Day"), help_text=_("day of month or distance from Easter in days")
    )
    month = models.IntegerField(_("Month"), null=True, blank=True)
    year = models.IntegerField(_("Year"), null=True, blank=True)

    class Meta:
        verbose_name = _("Calculated Holiday")
        verbose_name_plural = _("Calculated Holidays")

    def __str__(self):
        if self.mode == "abs":
            return f"{self.name}: {self.day}.{self.month}.{self.year or ''}"
        if self.day >= 0:
            return f"{self.name}: {self.day} Tage nach Ostern"
        else:
            return f"{self.name}: {-self.day} Tage vor Ostern"

    def toJson(self):
        return {
            "name": self.name,
            "mode": self.mode,
            "day": self.day,
            "month": self.month or 0,
            "year": self.year or 0,
        }


class Region(models.Model):
    """Aggregates the usual holidays for that region"""

    name = models.CharField(_("Name"), max_length=50)
    shortname = models.CharField(_("Short Name"), max_length=10, unique=True)
    # holidays = models.ManyToManyField(Holiday, verbose_name=_('Holidays'),
    #                                   related_name='regions')
    calc_holidays = models.ManyToManyField(
        CalculatedHoliday, verbose_name=_("Holidays"), related_name="regions"
    )

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        ordering = ["name"]

    def __str__(self):
        return self.name


class FeedId(models.Model):
    """The Id for the URL of an ical feed"""

    uid = models.CharField("ID", max_length=20, unique=True)
    person = models.ForeignKey(
        Person, related_name="feed_ids", on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FeedId"
        verbose_name_plural = "FeedIds"

    def __str__(self):
        pass

    @classmethod
    def new(cls, person):
        """Return a new feed-id for a person.

        The old ones stay active
        """
        while True:
            try:
                uid = random_string(12, string.ascii_letters + string.digits)
                feed = FeedId.objects.create(uid=uid, person=person)
                return feed
            except IntegrityError:
                # uid was already taken
                pass
