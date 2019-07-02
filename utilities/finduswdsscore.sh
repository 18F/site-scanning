#!/bin/sh
# 
# This script will output a json document that has all of the USWDS scores for
# all of the domains that the scanner knows about.
# 

if [ -z "$SCANNERHOST" ] ; then
	echo "error:  set the SCANNERHOST environment variable to make this work"
	exit 1
fi

echo '['
curl -s "https://${SCANNERHOST}/api/v1/scans/uswds2/" | jq -r '.[] | .scan_data_url' | while read line ; do
	curl -s "$line" | jq -c '{total_score: .total_score, domain: .domain}'
done
echo ']'

