from django.contrib import admin

from .models import Person, Ward, ChangingStaff

admin.site.register(Person)
admin.site.register(Ward)
admin.site.register(ChangingStaff)
