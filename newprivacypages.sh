#!/bin/sh
#
# This script will look at the differences between the last N days of present
# privacy pages and emit a list of domains that have new/removed pages.
#
# If you supply an argument, it will try to compare N days back.  If you do not
# supply an argument, it will compare 20 days back.
#
# usage examples:
#    ./newprivacypages.sh
#    ./newprivacypages.sh 5
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
	DAYSAGO=20
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

#curl -s "https://site-scanning.app.cloud.gov/privacy/json/?date=${TODAY}&present=Present" | jq -r '.[] | .domain' | sort > /tmp/todaydomains.$$
#curl -s "https://site-scanning.app.cloud.gov/privacy/json/?date=${EARLIER}present=Present" | jq -r '.[] | .domain' | sort > /tmp/earlierdomains.$$

curl -s "https://site-scanning.app.cloud.gov/api/v1/date/${TODAY}/scans/privacy/?data.status_code=200" | jq -r '.[] | .domain' | sort > /tmp/todaydomains.$$
curl -s "https://site-scanning.app.cloud.gov/api/v1/date/${EARLIER}/scans/privacy/?data.status_code=200" | jq -r '.[] | .domain' | sort > /tmp/earlierdomains.$$

echo "# Comparing $EARLIER with $TODAY:"
diff /tmp/earlierdomains.$$ /tmp/todaydomains.$$

rm -f /tmp/earlierdomains.$$ /tmp/todaydomains.$$
