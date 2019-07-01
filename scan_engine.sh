#!/bin/sh
#
# This script is what gets the list of domains to scan, 
# runs the scanners, collects the data, and puts it into s3.
# It also cleans up old scans (>1y) to prevent clutter.
#
# It is meant to be run like so:
#   cf run-task scanner-ui /app/scan_engine.sh

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
	git clone https://github.com/18F/domain-scan
fi
cd domain-scan

# XXX When we get this branch merged, remove this.
git checkout tspencer/200scanner

pip3 install -r requirements.txt
pip3 install -r requirements-scanners.txt

# get the list of domains
# XXX this is a subset of the list that we can use for testing
# cat <<EOF > /tmp/domains.csv
# Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email
# DATA.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,(blank)
# 18F.GOV,Federal Agency - Executive,General Services Administration,18F,Washington,DC,tts-vulnerability-reports@gsa.gov
# GSA.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
# USA.GOV,Federal Agency - Executive,General Services Administration,Office of Citizen Services and Communications,Washington,DC,(blank)
# DIGITAL.GOV,Federal Agency - Executive,General Services Administration,The General Services Administration,Washington,DC,(blank)
# FEDRAMP.GOV,Federal Agency - Executive,General Services Administration,Office of Citizen Services and Innovative Technologies,Washington,DC,(blank)
# ACQUISITION.GOV,Federal Agency - Executive,General Services Administration,Integrated Acquisition Environment,Arlington,VA,(blank)
# CIO.GOV,Federal Agency - Executive,General Services Administration,Chief Information Officers Council,Washington,DC,(blank)
# IDMANAGEMENT.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,(blank)
# PERFORMANCE.GOV,Federal Agency - Executive,General Services Administration,GSA - Office of Citizen Services Innovative Technologies - OSCIT,Washington,DC,(blank)
# SECTION508.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,(blank)
# CPARS.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
# FBO.GOV,Federal Agency - Executive,General Services Administration,GSA/CAO/OAS,Arlington,VA,(blank)
# GSAADVANTAGE.GOV,Federal Agency - Executive,General Services Administration,US General Services Administration,Washington,DC,(blank)
# GSAAUCTIONS.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,ITServiceDesk@gsa.gov
# LOGIN.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,tts-vulnerability-reports@gsa.gov
# SAM.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Arlington,VA,(blank)
# EOF
wget -O /tmp/domains.csv https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv

# execute the scans
#./scan domains.csv --scan=200
./scan /tmp/domains.csv --scan=200 --workers=20

# make sure the credentials are set
AWS_ACCESS_KEY_ID=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.access_key_id')
export AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.secret_access_key')
export AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=$(echo "$VCAP_SERVICES" | jq -r '.s3[0].credentials.region')
export AWS_DEFAULT_REGION

# put scan results into s3
aws s3 cp cache/200/ "s3://$BUCKET/200/" --recursive
