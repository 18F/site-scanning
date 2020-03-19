#!/usr/bin/env python3
#
# This script will find all sites that have valid /coronavirus pages
#
import os
import requests

if 'APIHOST' in os.environ:
    apihost = os.environ['APIHOST']
else:
    apihost = 'site-scanning.app.cloud.gov'


# start a session up to make it more efficient to grab pages
session = requests.Session()


# use this to slurp the items on the pages down
def get_pages(url):
    first_page = session.get(url + '&page=1').json()
    for i in first_page['results']:
        yield i
    num_pages = int(first_page['count'] / 1000) + 1

    for page in range(2, num_pages):
        next_page = session.get(url + '&page=' + str(page)).json()
        for i in next_page['results']:
            yield i


domains = []
url = 'https://' + apihost + '/api/v1/scans/200scanner/?page_size=1000&data.%2Fcoronavirus=200'
for page in get_pages(url):
    domains.append(page['domain'])

print('# domains with valid /coronavirus pages')
for i in domains:
    print(i)
