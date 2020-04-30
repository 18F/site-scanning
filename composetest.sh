#!/bin/sh
#
# This script configures environment variables, loads data into our environment,
# and then runs tests.
#

# function to give us a way to exit early and clean up if need be.
cleanup()
{
	if [ -z "$1" ] ; then
		exit 0
	else
		echo "failed: $1"
		exit 1
	fi
}

# set up environment
aws "$S3ENDPOINT" s3 mb "s3://$BUCKETNAME"
./manage.py migrate || cleanup "could not do db migrations"

# load data into our environment
export BATCHSIZE=4
export DOMAINCSV="/tmp/testdomains.csv"
cat <<EOF > "$DOMAINCSV"
Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email
18F.GOV,Federal Agency - Executive,General Services Administration,18F,Washington,DC,tts-vulnerability-reports@gsa.gov
GSA.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
AFRH.GOV,Federal Agency - Executive,Armed Forces Retirement Home,Armed Forces Retirement Home,Washington,DC,(blank)
CLOUD.GOV,Federal Agency - Executive,General Services Administration,18F | GSA,Washington,DC,tts-vulnerability-reports@gsa.gov
LOGIN.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,tts-vulnerability-reports@gsa.gov
calendar.gsa.gov,,,,,,
*.ecmapps.treasuryecm.gov,,,,,,
EOF
./scan_engine.sh

# run app test suite
./manage.py test || cleanup "python test suite exited uncleanly"

SCANTYPES="
	pagedata
	200scanner
	uswds2
	sitemap
	privacy
	dap
	third_parties
	lighthouse
"

# do a test that checks if the s3 bucket contains data
echo "checking what is in the s3 bucket"
for i in $SCANTYPES ; do
	aws "$S3ENDPOINT" s3 ls "s3://$BUCKETNAME/$i/" | grep 18f.gov >/dev/null || cleanup "$i s3 bucket does not contain the 18f.gov scan"
done

# test that there are indexes available
echo "checking whether indexes were created"
for i in $SCANTYPES ; do
	curl -s "$ESURL"/_cat/indices?v | grep $i >/dev/null || cleanup "the $i index was not created"
done

# everything must be great!
cleanup
