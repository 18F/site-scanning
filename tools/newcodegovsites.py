#!/usr/bin/env python3
#
# This script will look at the differences between the last N days of present
# code.json files and emit a list of new domains.
#
# If you supply an argument, it will try to compare N days back.  If you do not
# supply an argument, it will compare 20 days back.
#
# usage examples:
#    ./newcodegovsites.py
#    ./newcodegovsites.py 5
#
import os
import sys
import datetime
import requests

if 'APIHOST' in os.environ:
    apihost = os.environ['APIHOST']
else:
    apihost = 'site-scanning.app.cloud.gov'


try:
    score = str(sys.argv[1])
except IndexError:
    score = str(50)

try:
    daysago = int(sys.argv[2])
except IndexError:
    daysago = 20

today = datetime.date.today()
earlier = today - datetime.timedelta(days=daysago)

dateurl = 'https://' + apihost + '/api/v1/lists/dates/'
r = requests.get(dateurl)
dates = r.json()

# if we don't have today, take the first one
if str(today) not in dates:
    today = datetime.date.fromisoformat(dates[0])

# if we don't have earlier, take the last one
if str(earlier) not in dates:
    earlier = datetime.date.fromisoformat(dates[-1])

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


todaydomains = []
todayurl = 'https://' + apihost + '/api/v1/date/' + str(today) + '/scans/200scanner/?page_size=100&data.%2Fcode%2F%2Fjson=200'
for page in get_pages(todayurl):
    todaydomains.append(page['domain'])

earlierdomains = []
earlierurl = 'https://' + apihost + '/api/v1/date/' + str(earlier) + '/scans/200scanner/?page_size=100&data.%2Fcode%2F%2Fjson=200'
for page in get_pages(earlierurl):
    earlierdomains.append(page['domain'])

newdomains = list(set(todaydomains) - set(earlierdomains))

print('# New domains with valid /code.json', 'between', today, 'and', earlier)
for i in newdomains:
    print(i)
