#!/bin/sh
#
# This script will look at the differences between the last N days of USWDS
# sites and display the sites that have changed (appeared or gone away)
#
# You will need to supply at least one argument, which is the score you
# want to filter on.
#
# If you supply a second argument, it will try to compare N days back.  If you do not
# supply a second argument, it will compare 5 days back.
#
# usage examples:
#    ./newcodegovsites.sh 50
#    ./newcodegovsites.sh 50 5
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
	echo "usage: $0 <score> [<daysago>]"
	exit 1
else
	SCORE="$1"
fi

if [ -z "$2" ] ; then
	DAYSAGO=5
else
	DAYSAGO="$2"
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

curl -s "https://site-scanning.app.cloud.gov/searchUSWDS/json/?date=${TODAY}&q=${SCORE}" | jq -r '.[] | .domain' | sort > /tmp/todaydomains.$$
curl -s "https://site-scanning.app.cloud.gov/searchUSWDS/json/?q=${SCORE}&date=${EARLIER}" | jq -r '.[] | .domain' | sort > /tmp/earlierdomains.$$

echo "# Comparing sites with a score over $SCORE - $EARLIER with $TODAY:"
diff /tmp/earlierdomains.$$ /tmp/todaydomains.$$

rm -f /tmp/earlierdomains.$$ /tmp/todaydomains.$$
