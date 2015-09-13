from datetime import date
from django.db import models
from django.utils.translation import ugettext as _


class Person(models.Model):
    name = models.CharField('Name', max_length=50)
    shortname = models.CharField('Short Name', max_length=10)
    start_date = models.DateField(default=date(2015, 1, 1),
        help_text='begin of job')
    end_date = models.DateField(default=date(2099, 12, 31),
        help_text='end of job')

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    def __str__(self):
        return self.name

    def toJson(self):
        res = {'name': self.name,
               'id': self.shortname}
        if self.start_date:
            res['start_date'] = self.start_date.strftime('%Y-%m-%d')
        if self.end_date:
            res['end_date'] = self.end_date.strftime('%Y-%m-%d')
        return res


class Ward(models.Model):
    name = models.CharField('Name', max_length=50)
    shortname = models.CharField('Short Name', max_length=10)
    max = models.IntegerField(help_text='maximum staffing')
    min = models.IntegerField(help_text='minimum staffing')
    nightshift = models.BooleanField(default=False,
        help_text='if True, staffing can not be planned on the next day.')
    everyday = models.BooleanField(default=False,
        help_text='if True, is to be planned also on free days.')
    continued = models.BooleanField(default=True,
        help_text='if True, then todays staffing will be planned for tomorrow')
    on_leave = models.BooleanField(default=False,
        help_text='if True, then persons planned for this are on leave')

    class Meta:
        verbose_name = _('Ward')
        verbose_name_plural = _('Wards')

    def __str__(self):
        return self.name


class ChangingStaff(models.Model):
    """*One person* is
    *added* to or *removed*
    on *one day*
    from the staffing of *one ward*
    """
    person = models.CharField('Person', max_length=10)
    ward = models.CharField('Ward', max_length=10)
    day = models.DateField()
    added = models.BooleanField()

    def toJson(self):
        return {
            'person': self.person,
            'ward': self.ward,
            'day': self.day.strftime('%Y%m%d'),
            'action': 'add' if self.added else 'remove',
        }

    def __str__(self):
        template = "Add {} to {} on {}" if self.added else "Remove {} from {} on {}"
        return template.format(self.person, self.ward, self.day.strftime('%Y-%m-%d'))
