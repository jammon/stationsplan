# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import date
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible


def date_to_json(date):
    return [date.year, date.month-1, date.day]


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10)

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
                                help_text=_('The top organizational unit'))

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
    company = models.ForeignKey(Company, related_name='wards')
    position = models.IntegerField(
        default=1,
        help_text=_('Ordering in the display'))
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
        return {'name': self.name,
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
                'approved': date_to_json(self.approved)
                            if self.approved else None,
                'id': self.id,
                'after_this': '' if not self.pk else ','.join(
                    self.after_this.values_list('shortname', flat=True)),
                }


@python_2_unicode_compatible
class Person(models.Model):
    ''' A person (worker) who can be planned for work
    '''
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField(_('Short Name'), max_length=10)
    start_date = models.DateField(_('start date'), default=date(2015, 1, 1),
                                  help_text=_('begin of job'))
    end_date = models.DateField(_('end date'), default=date(2099, 12, 31),
                                help_text=_('end of job'))
    departments = models.ManyToManyField(
        Department, verbose_name=_('Departments'), related_name='persons')
    company = models.ForeignKey(Company, related_name='persons', null=True)
    functions = models.ManyToManyField(
        Ward, related_name='staff', verbose_name=_('Wards'),
        help_text=_('Functions that he or she can  perform.'))
    position = models.IntegerField(
        _('position'),
        default=1,
        help_text=_('Ordering in the display'))

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
                }


@python_2_unicode_compatible
class ChangeLogging(models.Model):
    ''' Logs who has made which changes.
    '''
    company = models.ForeignKey(Company)
    user = models.ForeignKey(User)
    person = models.ForeignKey(Person)
    ward = models.ForeignKey(Ward)
    day = models.DateField()
    added = models.BooleanField()
    description = models.CharField(max_length=255)
    json = models.CharField(max_length=255)
    change_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day']

    def toJson(self):
        return {
            'person': self.person.shortname,
            'ward': self.ward.shortname,
            'day': self.day.strftime('%Y%m%d'),
            'action': 'add' if self.added else 'remove',
        }

    def save(self, *args, **kwargs):
        self.make_description()
        self.json = json.dumps(self.toJson())
        super(ChangeLogging, self).save(*args, **kwargs)

    def make_description(self):
        template = (
            '{user_name}: {self.person.name} ist {relation} {date} für '
            '{self.ward.name} {added}eingeteilt')
        self.description = template.format(
            user_name=self.user.last_name or self.user.get_username(),
            self=self,
            relation='ab' if self.ward.continued else 'am',
            date=self.day.strftime('%d.%m.%Y'),
            added='' if self.added else 'nicht mehr ')

    def __str__(self):
        return self.description


@python_2_unicode_compatible
class Employee(models.Model):
    ''' Somebody who uses the plan.
    Can be anyone who works there, but also other involved personnel,
    like management etc.
    '''
    user = models.OneToOneField(User, related_name='employee')
    departments = models.ManyToManyField(Department, related_name='employees')
    company = models.ForeignKey(Company, related_name='employees')

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
        help_text=_('Can be empty'))
    company = models.ForeignKey(
        Company, related_name='status_entries', null=True, blank=True,
        help_text=_('Can be empty'))

    def __str__(self):
        return '{}: {}'.format(self.name, self.content)
