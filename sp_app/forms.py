from django import forms
from django.contrib import admin
from django.utils.translation import ugettext as _

from .models import Person


class WardForm(forms.ModelForm):
    """ used in sp_app.admin.WardAdmin """
    staff = forms.ModelMultipleChoiceField(
        Person.objects.all(),
        # Add this line to use the double list widget
        widget=admin.widgets.FilteredSelectMultiple(
            _('Persons'), is_stacked=False),
        label=_('staff'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(WardForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            # if this is not a new object, we load related staff
            self.initial['staff'] = self.instance.staff.values_list(
                'pk', flat=True)
            self.fields['staff'].queryset = Person.objects.filter(
                company_id=self.instance.company_id)
        else:
            self.fields['staff'].queryset = Person.objects.none()

    def save(self, *args, **kwargs):
        instance = super(WardForm, self).save(*args, **kwargs)
        if instance.pk:
            for person in instance.staff.all():
                if person not in self.cleaned_data['staff']:
                    # we remove staff which have been unselected
                    instance.staff.remove(person)
            for person in self.cleaned_data['staff']:
                if person not in instance.staff.all():
                    # we add newly selected staff
                    instance.staff.add(person)
        return instance
