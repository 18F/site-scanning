#!/usr/bin/env python3
#
# merge $2 into $1 and output it into $3
#
import csv
import sys
from urllib.parse import urlparse
import tldextract


# This is the standard header format for the domains.csv file
fieldnames = ['Domain Name', 'Domain Type', 'Agency', 'Organization', 'City', 'State', 'Security Contact Email']

with open(sys.argv[3], 'w') as csvout:
    writer = csv.DictWriter(csvout, fieldnames=fieldnames)
    # writer.writeheader()
    domains = []
    agencyinfo = {}

    # open $1 and read/write it out
    with open(sys.argv[1]) as csvfile:
        domainfile = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in domainfile:
            domain = row['Domain Name']
            if domain.upper() not in map(str.upper, domains):
                domains.append(domain)

                # store agency info for the tld
                extract = tldextract.extract(domain)
                topleveldomain = extract.domain + '.' + extract.suffix
                agency = row['Agency']
                if agency != '' and topleveldomain not in agencyinfo.keys():
                    agencyinfo[topleveldomain.upper()] = agency
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
            if domain is None or domain == '':
                continue

            # If we already did this domain in this file, skip it
            if domain.upper() not in map(str.upper, domainlist):
                domainlist.append(domain)
                # if the previous file had the domain, skip it.
                if domain.upper() not in map(str.upper, domains):
                    newrow = {}

                    # make sure that it's the proper format
                    for i in fieldnames:
                        if i in row.keys():
                            newrow[i] = row[i]
                        else:
                            newrow[i] = ''
                    newrow['Domain Name'] = domain

                    # try to add agency info if we know the agency for the tld
                    if newrow['Agency'] == '':
                        extract = tldextract.extract(domain)
                        topleveldomain = extract.domain + '.' + extract.suffix
                        if topleveldomain.upper() in agencyinfo.keys():
                            newrow['Agency'] = agencyinfo[topleveldomain.upper()]

                    writer.writerow(newrow)
