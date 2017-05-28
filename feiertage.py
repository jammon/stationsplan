# -*- coding: utf-8 -*-
import csv
from six.moves.urllib.request import urlopen
from collections import defaultdict

currentyear = 2017
lastyear = 2020
url = "http://www.feiertage.net/csvfile.php?state={}&year={}&type=csv"
regions = {
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

holidays = defaultdict(list)
for region in regions.keys():
    for year in range(currentyear, lastyear + 1):
        link = url.format(region, year)
        # print("Read " + link)
        response = urlopen(link)
        cr = csv.reader(response)
        csvreader = csv.reader(response, delimiter=';')
        next(csvreader)
        for line in csvreader:
            # print(line)
            holidays[(line[0], line[1].lstrip())].append(region)

with open('holidays.csv', 'w') as output:
    csv_out = csv.writer(output)
    for (tag, name), val in holidays.items():
        csv_out.writerow((tag, name, '|'.join(val)))
