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
	dap
	third_parties
"

# This is where you set the repo/branch
DOMAINSCANREPO="https://github.com/18F/domain-scan"
BRANCH="tspencer/200scanner"

# How many days to keep around in the index
INDEXDAYS=30
NUMSCANS=$(echo "$SCANTYPES" | wc -l)
let "INDEXLINES=$INDEXDAYS * ($NUMSCANS - 2)"

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
echo "installing domain-scan:  this repo is big, so it can take a while"
if [ -d domain-scan ] ; then
	echo "found existing domain-scan dir, syncing it as a shortcut"
	cd domain-scan
	git checkout "$BRANCH"
else
	git clone --depth=1 --branch "$BRANCH" "$DOMAINSCANREPO"
	cd domain-scan
fi

# This is a little fragile in that if we ever change the order of the buildpacks or add more,
# this will need to be updated.
/home/vcap/deps/2/bin/python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-scanners.txt
pip3 install --upgrade --user awscli

# install more packages for the chrome headless stuff
# These _should_ be already installed by the apt buildpack, but this is here to ensure
# that the test environment gets them too.
apt-get update
apt-get install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget

# install node stuff for third_parties plugin
if [ -d ../node_modules ] ; then
	# npm install was already done by the buildpack, let's just use it and save time
	ln -s ../node_modules .
fi
npm install

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
curl -s "$ESURL/_cat/indices" | grep -E '[0-9]{4}-[0-9]{2}-[0-9]{2}-.+' | awk '{print $3}' | sort -rn | head -"$INDEXLINES" > /tmp/keepers
curl -s "$ESURL/_cat/indices" | grep -E '[0-9]{4}-[0-9]{2}-[0-9]{2}-.+' | awk '{print $3}' | while read line ; do
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
