#!/bin/sh
#
# This script will look at the differences between the last 5 days of present
# code.json files and emit a list of new/removed domains
#

YESTERDAY="$(date -v-5d +%F)"
if [ "$?" -gt 0 ] ; then
	YESTERDAY="$(date -d "yesterday 13:00" '+%Y-%m-%d')"
fi

TODAY="$(date '+%F')"
if [ "$?" -gt 0 ] ; then
	TODAY="$(date -d '+%Y-%m-%d')"
fi

curl -s "https://site-scanning.app.cloud.gov/search200/json/?200page=/code.json&date=${TODAY}&mimetype=application/json&present=Present" | jq -r '.[] | .domain' | sort > /tmp/todaydomains.$$
curl -s "https://site-scanning.app.cloud.gov/search200/json/?200page=/code.json&date=${YESTERDAY}&mimetype=application/json&present=Present" | jq -r '.[] | .domain' | sort > /tmp/yesterdaydomains.$$

echo "# Comparing $YESTERDAY with $TODAY:"
diff /tmp/yesterdaydomains.$$ /tmp/todaydomains.$$

rm -f /tmp/yesterdaydomains.$$ /tmp/todaydomains.$$
