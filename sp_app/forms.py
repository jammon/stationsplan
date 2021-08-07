from django.forms import (widgets, ModelForm, ModelMultipleChoiceField,
                          MultipleChoiceField, CheckboxSelectMultiple,
                          BooleanField)
from django.contrib import admin
from django.utils.translation import gettext as _

from .models import Person, Ward, Department


class WardAdminForm(ModelForm):
    """ used in sp_app.admin.WardAdmin

    Restricts staffing to Persons of the same Company
    """
    staff = ModelMultipleChoiceField(
        Person.objects.all(),
        # Add this line to use the double list widget
        widget=admin.widgets.FilteredSelectMultiple(
            _('Persons'), is_stacked=False),
        label=_('staff'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(WardAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            # if this is not a new object, we load related staff
            self.initial['staff'] = self.instance.staff.values_list(
                'pk', flat=True)
            self.fields['staff'].queryset = Person.objects.filter(
                company_id=self.instance.company_id)
        else:
            self.fields['staff'].queryset = Person.objects.none()

    def save(self, *args, **kwargs):
        instance = super(WardAdminForm, self).save(*args, **kwargs)
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


class RowRadioboxSelect(widgets.Select):
    template_name = 'sp_app/row_radiobox_select.html'


class RowCheckboxSelectMultiple(CheckboxSelectMultiple):
    template_name = 'sp_app/row_checkbox_select.html'


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ['name', 'shortname', 'start_date', 'end_date', 'departments',
                  'position', 'company']
        widgets = {
            'position': RowRadioboxSelect,
            'departments': RowCheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('position', 'departments'):
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['departments'].queryset = Department.objects.filter(
            company__id=self.initial['company'])


class WardForm(ModelForm):
    wkdys = MultipleChoiceField(
        label='Wochentage',
        choices=(('1', 'Mo'), ('2', 'Di'), ('3', 'Mi'), ('4', 'Do'),
                 ('5', 'Fr'), ('6', 'Sa'), ('0', 'So')),
        widget=RowCheckboxSelectMultiple,
        required=False,
        help_text="Wenn kein Wochentag ausgewählt ist, wird die Funktion für "
        "alle üblichen Tage geplant.")
    inactive = BooleanField(
        label='Deaktiviert',
        required=False,
        help_text="Nicht mehr für die Planung verwenden.")

    class Meta:
        model = Ward
        fields = ['name', 'shortname', 'max', 'min', 'everyday', 'freedays',
                  'wkdys', 'weekdays', 'callshift', 'on_leave',
                  'departments', 'company', 'position',
                  'active', 'inactive',
                  # 'ward_type', 'approved', 'after_this', 'weight', 
                  ]
        widgets = {
            'departments': RowCheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['departments'].queryset = Department.objects.filter(
            company__id=self.initial['company'])

    def get_initial_for_field(self, field, field_name):
        if field_name == 'wkdys':
            return list(self.initial.get('weekdays', ''))
        if field_name == 'inactive':
            return not self.initial.get('active', True)
        return super().get_initial_for_field(field, field_name)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['weekdays'] = ''.join(self.cleaned_data.get('wkdys', []))
        cleaned_data['active'] = not cleaned_data['inactive']
