# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible


def date_to_json(date):
    return [date.year, date.month - 1, date.day]

FAR_FUTURE = date(2099, 12, 31)
ONE_DAY = timedelta(days=1)


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10)
    region = models.ForeignKey('Region', null=True, blank=True)
    extra_holidays = models.ManyToManyField(
        'Holiday', verbose_name=_('Holidays'), related_name='companies')

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Department(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10)
    company = models.ForeignKey(Company, related_name='departments',
                                help_text=_('The top organizational unit'),
                                on_delete=models.CASCADE,)

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Ward(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10)
    max = models.IntegerField(help_text=_('maximum staffing'))
    min = models.IntegerField(help_text=_('minimum staffing'))
    nightshift = models.BooleanField(
        _('nightshift'),
        default=False,
        help_text=_('if True, staffing can not be planned on the next day.'))
    everyday = models.BooleanField(
        _('everyday'),
        default=False,
        help_text=_('if True, is to be planned also on free days.'))
    freedays = models.BooleanField(
        _('freedays'),
        default=False,
        help_text=_('if True, is to be planned only on free days.'))
    continued = models.BooleanField(
        _('continued'),
        default=True,
        help_text=_('if True, '
                    'then todays staffing will be planned for tomorrow'))
    on_leave = models.BooleanField(
        _('on_leave'),
        default=False,
        help_text=_('if True, then persons planned for this are on leave'))
    departments = models.ManyToManyField(
        Department, verbose_name=_('Departments'), related_name='wards')
    company = models.ForeignKey(Company, related_name='wards',
                                on_delete=models.CASCADE)
    position = models.IntegerField(
        default=1,
        help_text=_('Ordering in the display'))
    ward_type = models.CharField(
        _('Ward type'), max_length=50, blank=True, default='',
        help_text=_('For sorting the CallTallies'))
    approved = models.DateField(
        null=True, blank=True,
        help_text=_('The date until which the plan is approved'))
    after_this = models.ManyToManyField(
        'self', symmetrical=False, blank=True,
        help_text=_('if not empty, '
                    'only these functions can be planned on the next day'))
    json = models.CharField(max_length=511)

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.json = json.dumps(self.toJson())
        super(Ward, self).save(*args, **kwargs)

    def toJson(self):
        res = {'name': self.name,
               'shortname': self.shortname,
               'min': self.min,
               'max': self.max,
               'nightshift': self.nightshift,
               'everyday': self.everyday,
               'freedays': self.freedays,
               'continued': self.continued,
               'on_leave': self.on_leave,
               'company_id': self.company_id,
               'position': self.position,
               'after_this': '' if not self.pk else ','.join(
                   self.after_this.values_list('shortname', flat=True)),
               'ward_type': self.ward_type}
        if self.approved is not None:
            res['approved'] = date_to_json(self.approved)
        return res

    def clean(self):
        # A ward should not have the shortname id
        if self.shortname == 'id':
            raise ValidationError({
                'shortname': _('Wards cannot have the shortname "id".')})
        # A ward should not have the shortname id
        if ',' in self.shortname:
            raise ValidationError({
                'shortname': _('Wards cannot have a comma in their shortname.')
            })


@python_2_unicode_compatible
class Person(models.Model):
    ''' A person (worker) who can be planned for work
    '''
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10)
    start_date = models.DateField(_('start date'), default=date(2015, 1, 1),
                                  help_text=_('begin of job'))
    end_date = models.DateField(_('end date'), default=FAR_FUTURE,
                                help_text=_('end of job'))
    departments = models.ManyToManyField(
        Department, verbose_name=_('Departments'), related_name='persons')
    company = models.ForeignKey(Company, related_name='persons', null=True,
                                on_delete=models.CASCADE)
    functions = models.ManyToManyField(
        Ward, related_name='staff', verbose_name=_('Tasks'),
        help_text=_('Functions that he or she can  perform.'))
    position = models.IntegerField(
        _('position'),
        default=1,
        help_text=_('Ordering in the display'))
    anonymous = models.BooleanField(
        _('Anonymous'),
        default=False,
        help_text=_('if True this person represents multiple other persons, '
                    'e.g. an appartment'))

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    def __str__(self):
        return self.name

    def toJson(self):
        return {'name': self.name,
                'id': self.shortname,
                'start_date': date_to_json(self.start_date),
                'end_date': date_to_json(self.end_date),
                'functions': [f.shortname for f in self.functions.all()],
                'position': self.position,
                'anonymous': self.anonymous,
                }

    def save(self, *args, **kwargs):
        super(Person, self).save(*args, **kwargs)
        # when a person leaves, their plannings should stop
        if self.end_date < FAR_FUTURE:
            Planning.objects.filter(
                person=self,
                start__gte=self.end_date).delete()
            Planning.objects.filter(
                person=self,
                end__gt=self.end_date).update(end=self.end_date)


@python_2_unicode_compatible
class ChangeLogging(models.Model):
    ''' Logs who has made which changes.
    The change can be for one day (continued==False) or continued
    If continued==True it can have an end date (`until`)
    '''
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    day = models.DateField()
    added = models.BooleanField()
    continued = models.BooleanField(
        default=True,
        help_text='If False the change is valid for one day.')
    until = models.DateField(
        null=True, blank=True,
        help_text='The last day the change is valid. Can be blank.')
    description = models.CharField(max_length=255)
    json = models.CharField(max_length=255)
    change_time = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0)
    current_version = 1

    class Meta:
        verbose_name = _('ChangeLogging')
        verbose_name_plural = _('ChangeLoggings')

    def toJson(self):
        data = {
            'person': self.person.shortname,
            'ward': self.ward.shortname,
            'day': self.day.strftime('%Y%m%d'),
            'action': 'add' if self.added else 'remove',
            'continued': self.continued,
        }
        if self.until:
            data['until'] = self.until.strftime('%Y%m%d')
        return data

    def make_json(self):
        self.json = json.dumps(self.toJson())

    def calc_data(self):
        self.make_description()
        self.make_json()
        self.version = self.current_version
        return self

    def save(self, *args, **kwargs):
        self.calc_data()
        super(ChangeLogging, self).save(*args, **kwargs)

    def make_description(self):
        template = (
            '{user_name}: {self.person.name} ist {relation} {date}{until} '
            '{added}für {self.ward.name} eingeteilt')
        self.description = template.format(
            user_name=self.user.last_name or self.user.get_username(),
            self=self,
            relation='ab' if self.continued else 'am',
            date=self.day.strftime('%d.%m.%Y'),
            until=(' bis {}'.format(self.until.strftime('%d.%m.%Y'))
                   if self.until else ''),
            added='' if self.added else 'nicht mehr ')

    def __str__(self):
        return self.description


def process_change(cl):
    """ Weave the change into the existing Plannings.

    Return the json dict of the effective change to be returned to the client.
    """
    plannings = Planning.objects.filter(person_id=cl.person_id,
                                        ward_id=cl.ward_id)
    pl_data = dict(person_id=cl.person_id, ward_id=cl.ward_id)
    if cl.added:
        if cl.continued:
            end = cl.until or FAR_FUTURE
            plannings = list(plannings.filter(
                end__gte=cl.day,
                start__lte=end,
            ).order_by('start'))
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
                    return {}     # change is in an existing planning
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
            start__lte=cl.until or cl.day, end__gte=cl.day).order_by('start')
        if len(plannings) == 0:
            return {}
        if cl.continued:
            if cl.until:
                for pl in plannings:
                    if pl.start < cl.day:
                        if pl.end > cl.until:
                            Planning.objects.create(start=cl.until + ONE_DAY,
                                                    end=pl.end, **pl_data)
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
                        Planning.objects.create(start=cl.day + ONE_DAY,
                                                end=pl.end,
                                                **pl_data)
                    pl.end = cl.day - ONE_DAY
                    pl.save()

    return json.loads(cl.json)


@python_2_unicode_compatible
class Planning(models.Model):
    """ One time period, where one person is planned for one ward.

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
        'self', on_delete=models.SET_NULL, blank=True, null=True,
        related_name='supersedes', default=None,
        help_text=_("Later planning that supersedes this one"))

    class Meta:
        verbose_name = _('Planning')
        verbose_name_plural = _('Plannings')

    def toJson(self):
        return {
            'person': self.person.shortname,
            'ward': self.ward.shortname,
            'start': self.start.strftime('%Y%m%d'),
            'end': self.end.strftime('%Y%m%d'),
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
        one_sided = ("{0.person.name} ist ab {0.start:%d.%m.%Y} "
                     "für {0.ward.name} geplant.")
        two_sided = ("{0.person.name} ist von {0.start:%d.%m.%Y} bis "
                     "{0.end:%d.%m.%Y} für {0.ward.name} geplant.")
        if self.end == FAR_FUTURE:
            return one_sided.format(self)
        return two_sided.format(self)


@python_2_unicode_compatible
class Employee(models.Model):
    ''' Somebody who uses the plan.
    Can be anyone who works there, but also other involved personnel,
    like management etc.
    '''
    user = models.OneToOneField(User, related_name='employee',
                                on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department, related_name='employees')
    company = models.ForeignKey(Company, related_name='employees',
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')

    def __str__(self):
        return '{}, {}, {}'.format(
            self.user.get_full_name() or self.user.get_username(),
            ', '.join([d.name for d in self.departments.all()]),
            self.company.name)


@python_2_unicode_compatible
class StatusEntry(models.Model):
    ''' Saves some detail about the current status of the planning
    or the program
    '''
    name = models.CharField(max_length=30)
    content = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department, related_name='status_entries', null=True, blank=True,
        help_text=_('Can be empty'), on_delete=models.SET_NULL)
    company = models.ForeignKey(
        Company, related_name='status_entries', null=True, blank=True,
        help_text=_('Can be empty'), on_delete=models.SET_NULL)

    def __str__(self):
        return '{}: {}'.format(self.name, self.content)


@python_2_unicode_compatible
class Holiday(models.Model):
    date = models.DateField(_('Datum'))
    name = models.CharField(_('Name'), max_length=50)

    def __str__(self):
        return '{}: {}'.format(self.date, self.name)


@python_2_unicode_compatible
class Region(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10, unique=True)
    holidays = models.ManyToManyField(Holiday, verbose_name=_('Holidays'),
                                      related_name='regions')

    def __str__(self):
        return self.name
