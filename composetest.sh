#!/bin/sh
# 
# This script configures environment variables, starts up a local test environment,
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
export DOMAINCSV="/tmp/testdomains.csv"
cat <<EOF > "$DOMAINCSV"
Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email
18F.GOV,Federal Agency - Executive,General Services Administration,18F,Washington,DC,tts-vulnerability-reports@gsa.gov
GSA.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
EOF
./scan_engine.sh "$BUCKETNAME"


# run app test suite
./manage.py test || cleanup "python test suite exited uncleanly"

# do a test that checks if the s3 bucket contains data
echo "checking what is in the s3 bucket"
aws "$S3ENDPOINT" s3 ls "s3://$BUCKETNAME/privacy/" | grep 18f.gov >/dev/null || cleanup "s3 bucket does not contain a selected scan"

# test that there are indexes available
echo "checking whether indexes were created"
curl -s "$ESURL"/_cat/indices?v | grep pagedata >/dev/null || cleanup "the pagedata index was not created"

# everything must be great!
cleanup
