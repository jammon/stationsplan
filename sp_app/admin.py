from django.contrib import admin

from .models import (Person, Ward, ChangingStaff, Department,
                     Company, Employee)

admin.site.register(Person)
admin.site.register(Ward)
admin.site.register(ChangingStaff)
admin.site.register(Department)
admin.site.register(Company)
admin.site.register(Employee)
