#!/bin/sh
# 
# This script will output a json document that has all of the USWDS scores for
# all of the domains that the scanner knows about.
#
# It takes about 8 minutes to run, so you should probably output it into a file
# and then use jq to operate on it like so:
#
# SCANNERHOST=SCANNERHOST.app.cloud.gov utilities/finduswdsscore.sh > /tmp/scores.json
# cat /tmp/scores.json | jq -c 'select(.total_score > 1)' | wc -l
# cat /tmp/scores.json | jq -c 'select(.total_score > 10)'
# 

if [ -z "$SCANNERHOST" ] ; then
	echo "error:  set the SCANNERHOST environment variable to make this work"
	exit 1
fi

curl -s "https://${SCANNERHOST}/api/v1/scans/uswds2/" | jq -r '.[] | .scan_data_url' | while read line ; do
	curl -s "$line" | jq -c '{total_score: .total_score, domain: .domain}'
done
