#!/bin/sh
#
# This script is what gets the list of domains to scan, 
# runs the scanners, collects the data, and puts it into s3.
# It also cleans up old scans (>30 days) to prevent clutter.
#
# It is meant to be run like so:
#   cf run-task scanner-ui /app/scan_engine.sh

# This is where you add more scan types
SCANTYPES="
	200scanner
	uswds2
"

# This is where you set the repo/branch
DOMAINSCANREPO="https://github.com/18F/domain-scan"
BRANCH="tspencer/200scanner"

# How many days to keep around in the index
INDEXDAYS=30

# set up variables that you need to get this to run as a task.
export PYTHONPATH=/home/vcap/deps/0
export PATH=/home/vcap/deps/0/bin:/usr/local/bin:/usr/bin:/bin:/home/vcap/app/.local/bin:$PATH
export LD_LIBRARY_PATH=/home/vcap/deps/0/lib
export LIBRARY_PATH=/home/vcap/deps/0/lib

# make sure we have all the arguments we need
if [ -n "$1" ] ; then
	BUCKET="$1"
else
	BUCKET=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.bucket')
	if [ -z "$BUCKET" ] ; then
		echo "no bucket supplied"
		echo "usage:    $0 <s3 bucket name>"
		echo "example:  $0 scanbucket"
		exit 1
	fi
fi

cd /app

# install aws cli
pip3 install awscli --upgrade --user

# set up domain-scan
if [ ! -d domain-scan ] ; then
	echo installing domain-scan
	git clone "$DOMAINSCANREPO"
fi
cd domain-scan
git checkout "$BRANCH"
pip3 install -r requirements.txt
pip3 install -r requirements-scanners.txt

# get the list of domains
wget -O /tmp/domains.csv https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv

# execute the scans
echo -n "Scan start: "
date
for i in ${SCANTYPES} ; do
	if [ -z "$SCANLIST" ] ; then
		SCANLIST="$i"
	else
		SCANLIST="$i,$SCANLIST"
	fi
done
./scan /tmp/domains.csv --scan="$SCANLIST"

# make sure the credentials are set
AWS_ACCESS_KEY_ID=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.access_key_id')
export AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.secret_access_key')
export AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.region')
export AWS_DEFAULT_REGION

# put scan results into s3
for i in ${SCANTYPES} ; do
	aws s3 cp "cache/$i/" "s3://$BUCKET/$i/" --recursive
done

# put scan results into ES
ESURL=$(echo "$VCAP_SERVICES" | jq -r '.elasticsearch56[0].credentials.uri')
for i in ${SCANTYPES} ; do
	for j in cache/"$i"/*.json ; do
		DOMAIN=$(basename -s .json "$j")
		DATE=$(date +%Y-%m-%dT%H:%M:%SZ)
		SHORTDATE=$(date +%Y-%m-%d)

		# add metadata
		echo "{\"domain\":\"$DOMAIN\",\"scantype\":\"$i\",\"data\":" > /tmp/scan.json
		cat "$j" >> /tmp/scan.json
		echo ",\"scan_data_url\":\"https://s3-$AWS_DEFAULT_REGION.amazonaws.com/$BUCKET/$i/$DOMAIN.json\",\"lastmodified\":\"$DATE\"}" >> /tmp/scan.json
		jq . /tmp/scan.json > /tmp/prettyscan.json

		# slurp the data in
		curl -s -XPOST "$ESURL/$SHORTDATE-$i/scan" -d @/tmp/prettyscan.json
		echo
	done
done

# delete old indexes in ES
curl -s "$ESURL/_cat/indices" | awk '{print $3}' | sort -rn | head -"$INDEXDAYS" > /tmp/keepers
curl -s "$ESURL/_cat/indices" | awk '{print $3}' | while read line ; do
	if echo "$line" | grep -Ff /tmp/keepers >/dev/null ; then
		echo keeping "$line" index
	else
		echo deleting "$line" index
		curl -s -X DELETE "$ESURL/$line"
		echo
	fi
done

echo -n "Scan end: "
date
