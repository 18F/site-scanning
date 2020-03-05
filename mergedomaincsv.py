#!/usr/bin/env python3
#
# merge $2 into $1 and output it into $3
#
import csv
import sys
from urllib.parse import urlparse


# This is the standard header format for the domains.csv file
fieldnames = ['Domain Name', 'Domain Type', 'Agency', 'Organization', 'City', 'State', 'Security Contact Email']

with open(sys.argv[3], 'w') as csvout:
    writer = csv.DictWriter(csvout, fieldnames=fieldnames)
    # writer.writeheader()
    domains = []

    # open $1 and read/write it out
    with open(sys.argv[1]) as csvfile:
        domainfile = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in domainfile:
            domain = row['Domain Name']
            if domain not in domains:
                domains.append(domain)
            writer.writerow(row)

    # open $2 and read/write it out, discarding duplicates
    with open(sys.argv[2]) as csvfile:
        domainfile = csv.DictReader(csvfile)
        domainlist = []
        for row in domainfile:
            # the new file might not have the same header.  Assuming that first
            # field is the domain, if it's not 'Domain Name'.  Also try 'URL'.
            if 'Domain Name' in row.keys():
                domain = row['Domain Name']
            elif 'URL' in row.keys():
                domain = urlparse(row['URL']).hostname
            else:
                domain = row[list(row.keys())[0]]
            if domain == '':
                next

            # If we already did this domain in this file, skip it
            if domain not in domainlist:
                domainlist.append(domain)
                # if the previous file had the domain, skip it.
                if domain not in domains:
                    newrow = {}
                    # make sure that it's the proper format
                    for i in fieldnames:
                        if i in row.keys():
                            newrow[i] = row[i]
                        else:
                            newrow[i] = ''
                    newrow['Domain Name'] = domain
                    writer.writerow(newrow)
