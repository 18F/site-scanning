#!/bin/sh
#
# This script is what gets the list of domains to scan, 
# runs the scanners, collects the data, and puts it into s3.
# It also cleans up old scans (>30 days) to prevent clutter.
#
# It is meant to be run like so:
#   cf run-task scanner-ui /app/scan_engine.sh -m 2048M

# This is where you add more scan types
SCANTYPES="
	pagedata
	200scanner
	uswds2
	sitemap
	privacy
"

# This is where you set the repo/branch
DOMAINSCANREPO="https://github.com/18F/domain-scan"
#BRANCH="tspencer/200scanner"
# XXX temporary
BRANCH="tspencer/finalurlinsamedomain"

# How many days to keep around in the index
INDEXDAYS=30

# set up variables that you need to get this to run as a task.
export PYTHONPATH=/home/vcap/deps/0
export PATH=/home/vcap/deps/0/bin:/usr/local/bin:/usr/bin:/bin:/home/vcap/app/.local/bin:$PATH
export LD_LIBRARY_PATH=/home/vcap/deps/0/lib
export LIBRARY_PATH=/home/vcap/deps/0/lib

# make sure the credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] ; then
	AWS_ACCESS_KEY_ID=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.access_key_id')
	export AWS_ACCESS_KEY_ID
fi
if [ -z "$AWS_SECRET_ACCESS_KEY" ] ; then
	AWS_SECRET_ACCESS_KEY=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.secret_access_key')
	export AWS_SECRET_ACCESS_KEY
fi
if [ -z "$AWS_DEFAULT_REGION" ] ; then
	AWS_DEFAULT_REGION=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.region')
	export AWS_DEFAULT_REGION
fi
if [ -z "$ESURL" ] ; then
	ESURL=$(echo "$VCAP_SERVICES" | jq -r '.elasticsearch56[0].credentials.uri')
fi

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

# set up domain-scan
echo installing domain-scan
git clone --depth=1 --branch "$BRANCH" "$DOMAINSCANREPO"
cd domain-scan
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-scanners.txt

# install aws cli
pip3 install awscli --upgrade --user

# get the list of domains
if [ -f "$DOMAINCSV" ] ; then
	# this is so we can supply our own file for testing
	cp "$DOMAINCSV" /tmp/domains.csv
else
	wget -O /tmp/domains.csv https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv
fi

# clean up old scans (if there are any)
if [ -d ./cache ] ; then
	rm -rf cache
	mkdir cache
fi

# execute the scans
# XXX someday, we should restructure this so that it processes these domains
# XXX in batches of 2000 or so:  trying to do 100k domains will run out of disk space
echo "Scan start: $(date)"
for i in ${SCANTYPES} ; do
	if ./scan /tmp/domains.csv --scan="$i" ; then
		echo "scan of $i successful"
	else
		echo "scan of $i errored out for some reason"
	fi
done

# add metadata and put scan results into ES
echo "Adding metadata and loading scan results into elasticsearch.  This can take a while..."
for i in ${SCANTYPES} ; do
	echo "loading scantype: $i"
	# set the domain field to be a keyword rather than text so we can sort on it
	DATE=$(date +%Y-%m-%dT%H:%M:%SZ)
	SHORTDATE=$(date +%Y-%m-%d)
	echo '{"mappings": {"scan": {"properties": {"domain": {"type": "keyword"}}}}}' > /tmp/mapping.json
	if curl -s -XPUT "$ESURL/$SHORTDATE-$i" -d @/tmp/mapping.json | grep error ; then
		echo "problem creating mapping"
	fi

	# import all of the scans
	for j in cache/"$i"/*.json ; do
		DOMAIN=$(basename -s .json "$j")

		CSVLINE=$(grep -Ei "^$DOMAIN," /tmp/domains.csv)
		DOMAINTYPE=$(echo "$CSVLINE" | awk -F, '{print $2}' | tr -d \")
		AGENCY=$(echo "$CSVLINE" | awk -F, '{print $3}' | tr -d \")
		ORG=$(echo "$CSVLINE" | awk -F, '{print $4}' | tr '\\' '-' | tr -d \")

		# add metadata
		echo "{\"domain\":\"$DOMAIN\"," > /tmp/scan.json
		echo " \"scantype\":\"$i\"," >> /tmp/scan.json
		echo " \"domaintype\":\"$DOMAINTYPE\"," >> /tmp/scan.json
		echo " \"agency\":\"$AGENCY\"," >> /tmp/scan.json
		echo " \"organization\":\"$ORG\"," >> /tmp/scan.json
		echo " \"scan_data_url\":\"https://s3-$AWS_DEFAULT_REGION.amazonaws.com/$BUCKET/$i/$DOMAIN.json\"," >> /tmp/scan.json
		echo " \"lastmodified\":\"$DATE\"," >> /tmp/scan.json
		echo " \"data\":" >> /tmp/scan.json

		# This is because you cannot have . in field names in ES,
		# so we are replacing them with // for the document we are
		# going to index.
		cp /tmp/scan.json /tmp/noperiodsscan.json
		../deperiodkeys.py "$j" >> /tmp/noperiodsscan.json
		echo "}" >> /tmp/noperiodsscan.json

		# This is the document that will go into S3.
		cat "$j" >> /tmp/scan.json
		echo "}" >> /tmp/scan.json
		jq . /tmp/scan.json > "$j"

		# slurp the data in
		if curl -s -XPOST "$ESURL/$SHORTDATE-$i/scan" -d @/tmp/noperiodsscan.json | grep error ; then
			echo "problem importing $j: $(cat /tmp/noperiodsscan.json)"
		fi
	done
done

# delete old indexes in ES
curl -s "$ESURL/_cat/indices" | grep -E '[0-9]{4}-[0-9]{2}-[0-9]{2}-.*' | awk '{print $3}' | sort -rn | head -"$INDEXDAYS" > /tmp/keepers
curl -s "$ESURL/_cat/indices" | grep -vE '[0-9]{4}-[0-9]{2}-[0-9]{2}-.*' | awk '{print $3}' | while read line ; do
	if echo "$line" | grep -Ff /tmp/keepers >/dev/null ; then
		echo keeping "$line" index
	else
		echo deleting "$line" index
		curl -s -X DELETE "$ESURL/$line"
		echo
	fi
done

# put scan results into s3
for i in ${SCANTYPES} ; do
	echo "copying $i data to s3://$BUCKET/$i/"
	# The S3ENDPOINT thing is so we can send this to a local minio instance for testing
	if aws "$S3ENDPOINT" s3 cp "cache/$i/" "s3://$BUCKET/$i/" --recursive --only-show-errors ; then
		echo "copy of $i to s3 bucket successful"
	else
		echo "copy of $i to s3 bucket errored out"
	fi
done

echo "Scan end: $(date)"
