# -*- coding: utf-8 -*-
import csv
import os.path
import stationsplan
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from sp_app.models import Holiday, Region

REGIONS = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen"
}
filename = 'holidays.csv'


class Command(BaseCommand):
    help = 'Reads holidays from holidays.cvs'

    def handle(self, *args, **options):
        # Store regions
        regions = {}
        for shortname, name in REGIONS.items():
            regions[shortname] = Region.objects.get_or_create(
                name=name, shortname=shortname)[0]
        # Read holidays
        path = os.path.dirname(os.path.dirname(stationsplan.__file__))
        known_holidays = set(h.date for h in Holiday.objects.all())
        try:
            with open(os.path.join(path, filename)) as infile:
                csvreader = csv.reader(infile)
                for datestring, name, valid_regions in csvreader:
                    hdate = datetime.strptime(datestring, "%d.%m.%Y")
                    if hdate not in known_holidays:
                        holiday = Holiday.objects.create(
                            date=hdate, name=name)
                        for region in valid_regions.split('|'):
                            regions[region].holidays.add(holiday)

            self.stdout.write(self.style.SUCCESS(
                'Successfully imported holidays'))
        except (IOError, OSError):
            raise CommandError('File "%s" not found' % filename)
