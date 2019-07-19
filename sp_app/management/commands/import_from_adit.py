# -*- coding: utf-8 -*-
import json
import os.path
from collections import defaultdict
from datetime import date, datetime
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.models import LogEntry
from django.core.management.base import BaseCommand, CommandError
from sp_app.models import (
    Company, Department, Ward, DifferentDay, Person, 
    ChangeLogging, Planning, Employee, StatusEntry, Holiday, Region)

from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()

def get_datetime(fields, key):
    if fields.get(key) is None:
        return None
    return datetime.fromisoformat(fields[key][:19]),

class Command(BaseCommand):
    help = 'Imports fixture from the ADIT instance'

    def add_arguments(self, parser):
        parser.add_argument('fixture', type=open)

    def handle(self, *args, **options):
        infile = options['fixture']
        in_models = json.load(infile)
        model_dict = defaultdict(list)
        for item in in_models:
            if item["model"] != "sessions.session":
                model_dict[item["model"]].append(item)

        # delete old data
        self.stdout.write("delete old data")
        for klass in (Company, StatusEntry, Group, User, LogEntry, Holiday, Region):
            klass.objects.all().delete()
        # all other model should be deleted through the magic of on_delete=CASCADE
        # except StatusEntries

        # import holidays
        self.stdout.write("import holidays")
        holidays = [Holiday(
            pk=item["pk"],
            date=date.fromisoformat(item["fields"]["date"]),
            name=item["fields"]["name"],
        ) for item in model_dict["sp_app.holiday"]]
        Holiday.objects.bulk_create(holidays)

        # import regions
        self.stdout.write("import regions")
        for item in model_dict["sp_app.region"]:
            fields = item["fields"]
            region = Region.objects.create(
                pk=item["pk"],
                name=fields["name"],
                shortname=fields["shortname"],
            ) 
            region.holidays.add(*item["fields"]["holidays"])

        # import Companys
        self.stdout.write("import Companys")
        for item in model_dict["sp_app.company"]:
            fields = item["fields"]
            company = Company.objects.create(
                pk=item["pk"],
                name=fields["name"],
                shortname=fields["shortname"],
                region_id=fields["region"],
            ) 
            company.extra_holidays.add(*item["fields"]["extra_holidays"])

        # import Departments
        self.stdout.write("import Departments")
        departments = [Department(
            pk=item["pk"],
            name=item["fields"]["name"],
            shortname=item["fields"]["shortname"],
            company_id=item["fields"]["company"],
        ) for item in model_dict["sp_app.department"]]
        Department.objects.bulk_create(departments)

        # import Wards
        self.stdout.write("import Wards")
        after_this = []
        for item in model_dict["sp_app.ward"]:
            fields = item["fields"]
            ward = Ward.objects.create(
                pk=item["pk"],
                name=fields["name"],
                shortname=fields["shortname"],
                max=fields["max"],
                min=fields["min"],
                nightshift=fields["nightshift"],
                everyday=fields["everyday"],
                freedays=fields["freedays"],
                on_leave=fields["on_leave"],
                company_id=fields["company"],
                position=fields["position"],
                ward_type=fields["ward_type"],
                approved=None if fields["approved"] is None else date.fromisoformat(fields["approved"]),
                weight=fields["weight"],
            ) 
            ward.departments.add(*fields["departments"])
            if fields["after_this"]:
                after_this.append((ward, fields["after_this"]))
        for ward, a_t in after_this:
            ward.after_this.add(*a_t)

        # import differentdays
        self.stdout.write("import differentdays")
        differentdays = [DifferentDay(
            pk=item["pk"],
            day=date.fromisoformat(item["fields"]["day"]),
            ward_id=item["fields"]["ward"],
            added=item["fields"]["added"],
        ) for item in model_dict["sp_app.differentday"]]
        DifferentDay.objects.bulk_create(differentdays)

        # import Persons
        self.stdout.write("import Persons")
        for item in model_dict["sp_app.person"]:
            fields = item["fields"]
            person = Person.objects.create(
                pk=item["pk"],
                name=fields["name"],
                shortname=fields["shortname"],
                start_date=date.fromisoformat(fields["start_date"]),
                end_date=date.fromisoformat(fields["end_date"]),
                company_id=fields["company"],
                position=fields["position"],
                anonymous=fields["anonymous"],
            ) 
            person.departments.add(*fields["departments"])
            person.functions.add(*fields["functions"])

        # import Plannings
        self.stdout.write("import Plannings")
        plannings = [Planning(
            pk=item["pk"],
            company_id=item["fields"]["company"],
            person_id=item["fields"]["person"],
            ward_id=item["fields"]["ward"],
            start=date.fromisoformat(item["fields"]["start"]),
            end=date.fromisoformat(item["fields"]["end"]),
            json=item["fields"]["json"],
            superseded_by_id=item["fields"]["superseded_by"],
        ) for item in reversed(model_dict["sp_app.planning"])]
        Planning.objects.bulk_create(plannings)

        # create groups
        self.stdout.write("create groups")
        department_admins = Group.objects.create(name="Department admins") # 25-30
        department_admins.permissions.add(*Permission.objects.filter(
            codename__in=(
                "add_person", "change_person", "delete_person", 
                "add_ward", "change_ward", "delete_ward", 
            )))
        editor_group = Group.objects.create(name="Editors")
        editor_group.permissions.add(*Permission.objects.filter(
            codename__in=(
                "add_changelogging", "change_changelogging", "delete_changelogging", 
            )))

        # import Users
        self.stdout.write("import Users")
        for item in model_dict["auth.user"]:
            fields = item["fields"]
            user = User.objects.create(
                pk=item["pk"],
                password=fields["password"],
                last_login=fields["last_login"],
                username=fields["username"],
                first_name=fields["first_name"],
                last_name=fields["last_name"],
                email=fields["email"],
                is_staff=fields["is_staff"],
                is_active=fields["is_active"],
                date_joined=fields["date_joined"],
            ) 
            if fields["username"] in (
                    "jammon", "harbarth", "Beichl", "jean", "luerweg", "welp"):
                user.groups.add(editor_group)

        # import Employees
        self.stdout.write("import Employees")
        for item in model_dict["sp_app.employee"]:
            fields = item["fields"]
            employee = Employee.objects.create(
                pk=item["pk"],
                user_id=fields["user"],
                company_id=item["fields"]["company"],
            ) 
            employee.departments.add(*fields["departments"])

        # import ChangeLoggings
        self.stdout.write("import ChangeLoggings")
        changeloggings = [ChangeLogging(
            pk=item["pk"],
            company_id=item["fields"]["company"],
            user_id=item["fields"]["user"],
            person_id=item["fields"]["person"],
            ward_id=item["fields"]["ward"],
            day=date.fromisoformat(item["fields"]["day"]),
            added=item["fields"]["added"],
            continued=item["fields"]["continued"],
            until=get_datetime(fields, "until"),
            description=item["fields"]["description"],
            json=item["fields"]["json"],
            change_time=get_datetime(fields, "change_time"),
            version=item["fields"]["version"],
        ) for item in model_dict["sp_app.changelogging"]]
        ChangeLogging.objects.bulk_create(changeloggings)

        # import StatusEntrys
        self.stdout.write("import StatusEntrys")
        statusentrys = [StatusEntry(
            pk=item["pk"],
            company_id=item["fields"]["company"],
            name=item["fields"]["name"],
            content=item["fields"]["content"],
        ) for item in model_dict["sp_app.statusentry"]]
        StatusEntry.objects.bulk_create(statusentrys)

        # # import LogEntrys
        # self.stdout.write("import LogEntrys")
        # logentrys = [LogEntry(
        #     pk=item["pk"],
        #     action_time=datetime.fromisoformat(item["fields"]["action_time"][:19]),
        #     user_id=item["fields"]["user"],
        #     content_type_id=item["fields"]["content_type"],
        #     object_id=item["fields"]["object_id"],
        #     object_repr=item["fields"]["object_repr"],
        #     action_flag=item["fields"]["action_flag"],
        #     change_message=item["fields"]["change_message"],
        # ) for item in model_dict["admin.logentry"]]
        # LogEntry.objects.bulk_create(logentrys)
