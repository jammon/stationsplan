# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import date
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField('Short Name', max_length=10)

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Department(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    shortname = models.CharField('Short Name', max_length=10)
    company = models.ForeignKey(Company, related_name='departments',
                                help_text='The top organizational unit')

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return "{} ({})".format(self.name, self.company.name)


@python_2_unicode_compatible
class Person(models.Model):
    name = models.CharField('Name', max_length=50)
    shortname = models.CharField('Short Name', max_length=10)
    start_date = models.DateField(default=date(2015, 1, 1),
                                  help_text='begin of job')
    end_date = models.DateField(default=date(2099, 12, 31),
                                help_text='end of job')
    departments = models.ManyToManyField(Department, related_name='persons')
    company = models.ForeignKey(Company, related_name='persons', null=True)

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    def __str__(self):
        return self.name

    def toJson(self):
        def date_to_json(date):
            return [date.year, date.month-1, date.day]
        return {'name': self.name,
                'id': self.shortname,
                'start_date': date_to_json(self.start_date),
                'end_date': date_to_json(self.end_date), }


@python_2_unicode_compatible
class Ward(models.Model):
    name = models.CharField('Name', max_length=50)
    shortname = models.CharField('Short Name', max_length=10)
    max = models.IntegerField(help_text='maximum staffing')
    min = models.IntegerField(help_text='minimum staffing')
    nightshift = models.BooleanField(
        default=False,
        help_text='if True, staffing can not be planned on the next day.')
    everyday = models.BooleanField(
        default=False,
        help_text='if True, is to be planned also on free days.')
    continued = models.BooleanField(
        default=True,
        help_text='if True, then todays staffing will be planned for tomorrow')
    on_leave = models.BooleanField(
        default=False,
        help_text='if True, then persons planned for this are on leave')
    department = models.ManyToManyField(Department, related_name='wards')
    company = models.ForeignKey(Company, related_name='wards')

    class Meta:
        verbose_name = _('Ward')
        verbose_name_plural = _('Wards')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class ChangingStaff(models.Model):
    """*One person* is
    *added* to or *removed*
    on *one day*
    from the staffing of *one ward*
    """
    person = models.ForeignKey(Person)
    ward = models.ForeignKey(Ward)
    day = models.DateField()
    added = models.BooleanField()

    class Meta:
        ordering = ['day']

    def toJson(self):
        return {
            'person': self.person.shortname,
            'ward': self.ward.shortname,
            'day': self.day.strftime('%Y%m%d'),
            'action': 'add' if self.added else 'remove',
        }

    def __str__(self):
        template = ("Add {} to {} on {}" if self.added
                    else "Remove {} from {} on {}")
        return template.format(self.person.name, self.ward.name,
                               self.day.strftime('%Y-%m-%d'))


@python_2_unicode_compatible
class ChangeLogging(models.Model):
    """ Logs who has made which changes.
    Contains essentially the same information as ChangingStaff,
    but is handled differently.
    """
    company = models.ForeignKey(Company)
    user = models.ForeignKey(User)
    person = models.ForeignKey(Person)
    ward = models.ForeignKey(Ward)
    day = models.DateField()
    added = models.BooleanField()
    user_name = models.CharField(max_length=20)
    person_name = models.CharField(max_length=20)
    ward_name = models.CharField(max_length=20)
    ward_continued = models.BooleanField()

    def save(self, *args, **kwargs):
        self.user_name = self.user.get_full_name() or self.user.get_username()
        self.person_name = self.person.name
        self.ward_name = self.ward.name
        self.ward_continued = self.ward.continued
        super(ChangeLogging, self).save(*args, **kwargs)

    def __str__(self):
        template = (
            "{self.user_name}: {self.person_name} ist {relation} {date} für "
            "{self.ward_name} {added}eingeteilt")
        return template.format(
            self=self,
            relation="ab" if self.ward_continued else "am",
            date=self.day.strftime('%Y-%m-%d'),
            added="" if self.added else "nicht mehr ")


@python_2_unicode_compatible
class Employee(models.Model):
    user = models.OneToOneField(User, related_name='employee')
    departments = models.ManyToManyField(Department, related_name='employees')
    company = models.ForeignKey(Company, related_name='employees')

    def __str__(self):
        return "{}, {}, {}".format(
            self.user.get_full_name() or self.user.get_username(),
            ', '.join([d.name for d in self.departments.all()]),
            self.company.name)
