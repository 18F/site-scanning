#!/usr/bin/env python3
#
# find domains that were found by the third_party scan that were not
# already in our domain list.
#
# usage examples:
#    ./getscandomains.py
#
import os
import sys
import requests

if 'APIHOST' in os.environ:
    apihost = os.environ['APIHOST']
else:
    apihost = 'site-scanning.app.cloud.gov'


# Specify whether we want ssl or not
# Used to test against http://localhost:8000/, for example.
if '-nossl' in sys.argv:
    scheme = 'http'
else:
    scheme = 'https'


def chomp(s):
    return s.rstrip().lower()


# get old domain list before we start our session up and clean it up
olddomainlisturl = scheme + '://' + apihost + '/api/v1/lists/third_parties/values/domain/'
r = requests.get(olddomainlisturl)
d = r.json()
olddomains = list(map(chomp, d))

# start a session up to make it more efficient to grab pages
session = requests.Session()


# use this to slurp the items on the pages down
def get_pages(url):
    first_page = session.get(url + '?page=1').json()
    for i in first_page['results']:
        yield i
    num_pages = int(first_page['count'] / 100) + 1

    for page in range(2, num_pages):
        next_page = session.get(url + '?page=' + str(page)).json()
        for i in next_page['results']:
            yield i


domains = []
url = scheme + '://' + apihost + '/api/v1/scans/third_parties/'
for page in get_pages(url):
    try:
        for d in page['data']['page_domains']:
            # clean up the domains we found
            d = chomp(d)
            if d.endswith('.gov'):
                if d not in domains:
                    if d not in olddomains:
                        domains.append(d)
    except KeyError:
        continue

domains.sort()

print('Domain Name')
for i in domains:
    print(i)
