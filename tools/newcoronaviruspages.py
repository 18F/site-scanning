#!/usr/bin/env python3
#
# This script will look at the differences between the last N days of present
# /coronavirus pages and emit a list of new domains.
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

if "APIHOST" in os.environ:
    apihost = os.environ["APIHOST"]
else:
    apihost = "site-scanning.app.cloud.gov"


try:
    daysago = int(sys.argv[1])
except Exception:
    daysago = 20

# use this to specify whether we want sites that were
# redirected to other sites or not.  If not specified,
# get both.
samedomain = None
if "-samedomain" in sys.argv:
    samedomain = True
if "-notsamedomain" in sys.argv:
    samedomain = False

# if this is set, also include sites that redirect all pages
if "-allowredirectall" in sys.argv:
    allowredirectall = True
else:
    allowredirectall = False

# Specify whether we want ssl or not
# Used to test against http://localhost:8000/, for example.
if "-nossl" in sys.argv:
    scheme = "http"
else:
    scheme = "https"

today = datetime.date.today()
earlier = today - datetime.timedelta(days=daysago)

dateurl = scheme + "://" + apihost + "/api/v1/lists/dates/"
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
    first_page = session.get(url + "&page=1").json()
    for i in first_page["results"]:
        yield i
    num_pages = int(first_page["count"] / 100) + 1

    for page in range(2, num_pages):
        next_page = session.get(url + "&page=" + str(page)).json()
        for i in next_page["results"]:
            yield i


todaydomains = []
todayurl = (
    scheme
    + "://"
    + apihost
    + "/api/v1/date/"
    + str(today)
    + "/scans/pagedata/?page_size=100&data.%2Fcoronavirus.responsecode=200"
)
if samedomain is not None:
    if samedomain:
        todayurl = todayurl + "&data.%2Fcoronavirus.final_url_in_same_domain=true"
    else:
        todayurl = todayurl + "&data.%2Fcoronavirus.final_url_in_same_domain=false"
for page in get_pages(todayurl):
    if allowredirectall is False:
        if page["data"]["/redirecttest-foo-bar-baz"]["responsecode"] != "200":
            todaydomains.append(page["domain"])
    else:
        todaydomains.append(page["domain"])


earlierdomains = []
earlierurl = (
    scheme
    + "://"
    + apihost
    + "/api/v1/date/"
    + str(earlier)
    + "/scans/pagedata/?page_size=100&data.%2Fcoronavirus.responsecode=200"
)
if samedomain is not None:
    if samedomain:
        earlierurl = earlierurl + "&data.%2Fcoronavirus.final_url_in_same_domain=true"
    else:
        earlierurl = earlierurl + "&data.%2Fcoronavirus.final_url_in_same_domain=false"
for page in get_pages(earlierurl):
    if allowredirectall is False:
        if page["data"]["/redirecttest-foo-bar-baz"]["responsecode"] != "200":
            earlierdomains.append(page["domain"])
    else:
        earlierdomains.append(page["domain"])


newdomains = list(set(todaydomains) - set(earlierdomains))

print("# New domains with valid /coronavirus pages", "between", today, "and", earlier)
for i in newdomains:
    print(i)
