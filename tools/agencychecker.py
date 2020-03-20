#!/usr/bin/env python3
import csv
import sys


# This is the standard header format for the domains.csv file
fieldnames = ['Domain Name', 'Domain Type', 'Agency', 'Organization', 'City', 'State', 'Security Contact Email']

# open $1 and read/write it out
with open(sys.argv[1]) as csvfile:
    domainfile = csv.DictReader(csvfile, fieldnames=fieldnames)
    rows = 0
    rowswithagency = 0
    for row in domainfile:
        if row['Agency'] != '':
            rowswithagency = rowswithagency + 1
        rows = rows + 1
    print('total rows:', rows, 'rows with agency:', rowswithagency)
