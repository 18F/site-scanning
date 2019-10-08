#!/bin/sh
#
# This script will look at the differences between the last N days of present
# code.json files and emit a list of new/removed domains.
#
# If you supply an argument, it will try to compare N days back.  If you do not
# supply an argument, it will compare 7 days back.
#
# usage examples:
#    ./newcodegovsites.sh
#    ./newcodegovsites.sh 5
#

if command -v jq >/dev/null ; then
	echo "jq is here" >/dev/null
else
	echo "jq is required for this script to work.  Please install it (https://stedolan.github.io/jq/download/) and come back!"
	exit 1
fi

if command -v curl >/dev/null ; then
	echo "curl is here" >/dev/null
else
	echo "curl is required for this script to work.  Please install it and come back!"
	exit 2
fi

if [ -z "$1" ] ; then
	DAYSAGO=7
else
	DAYSAGO="$1"
fi

EARLIER="$(date -v-"$DAYSAGO"d +%F)"
if [ "$?" -gt 0 ] ; then
	NOW=$(date +%s)
	let SECONDS=86400*$DAYSAGO
	let EARLIER=$NOW-$SECONDS
	EARLIER="$(date -d "$EARLIER" -D '%s' '+%Y-%m-%d')"
fi

TODAY="$(date '+%F')"
if [ "$?" -gt 0 ] ; then
	TODAY="$(date -d '+%Y-%m-%d')"
fi

curl -s "https://site-scanning.app.cloud.gov/search200/json/?200page=/code.json&date=${TODAY}&mimetype=application/json&present=Present" | jq -r '.[] | .domain' | sort > /tmp/todaydomains.$$
curl -s "https://site-scanning.app.cloud.gov/search200/json/?200page=/code.json&date=${EARLIER}&mimetype=application/json&present=Present" | jq -r '.[] | .domain' | sort > /tmp/earlierdomains.$$

echo "# Comparing $EARLIER with $TODAY:"
diff /tmp/earlierdomains.$$ /tmp/todaydomains.$$

rm -f /tmp/earlierdomains.$$ /tmp/todaydomains.$$
