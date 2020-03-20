#!/usr/bin/env python3
#
# This script will find all sites that have valid /coronavirus pages
#
import os
import sys
import requests

if 'APIHOST' in os.environ:
    apihost = os.environ['APIHOST']
else:
    apihost = 'site-scanning.app.cloud.gov'

# use this to specify whether we want sites that were
# redirected to other sites or not.  If not specified,
# get both.
samedomain = None
if '-samedomain' in sys.argv:
    samedomain = True
if '-notsamedomain' in sys.argv:
    samedomain = False

# if this is set, also include sites that redirect all pages
if '-allowredirectall' in sys.argv:
    allowredirectall = True
else:
    allowredirectall = False

# Specify whether we want ssl or not
# Used to test against http://localhost:8000/, for example.
if '-nossl' in sys.argv:
    scheme = 'http'
else:
    scheme = 'https'

# start a session up to make it more efficient to grab pages
session = requests.Session()


# use this to slurp the items on the pages down
def get_pages(url):
    first_page = session.get(url + '&page=1').json()
    for i in first_page['results']:
        yield i
    num_pages = int(first_page['count'] / 100) + 1

    for page in range(2, num_pages):
        next_page = session.get(url + '&page=' + str(page)).json()
        for i in next_page['results']:
            yield i


domains = []
url = scheme + '://' + apihost + '/api/v1/scans/pagedata/?page_size=100&data.%2Fcoronavirus.responsecode=200'
if samedomain is not None:
    if samedomain:
        url = url + '&data.%2Fcoronavirus.final_url_in_same_domain=true'
    else:
        url = url + '&data.%2Fcoronavirus.final_url_in_same_domain=false'

for page in get_pages(url):
    if allowredirectall is False:
        if page['data']['/redirecttest-foo-bar-baz']['responsecode'] != '200':
            domains.append(page['domain'])
    else:
        domains.append(page['domain'])

print('# domains with valid /coronavirus pages')
for i in domains:
    print(i)
