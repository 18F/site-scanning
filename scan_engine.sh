#!/bin/sh
#
# This script is what gets the list of domains to scan, 
# runs the scanners, collects the data, and puts it into s3.
# It also cleans up old scans (>1y) to prevent clutter.
#

# make sure we have all the arguments we need
if [ -z "$1" ] ; then
	echo "no bucket supplied"
	echo "usage:    $0 <s3 bucket name>"
	echo "example:  $0 scanbucket"
	exit 1
fi
BUCKET="$1"

cd domain-scan

# get the list of domains
#https://github.com/GSA/data/raw/master/dotgov-domains/current-full.csv
#https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv
cat <<EOF > /tmp/domains.csv
Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email
DATA.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,(blank)
18F.GOV,Federal Agency - Executive,General Services Administration,18F,Washington,DC,tts-vulnerability-reports@gsa.gov
GSA.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
USA.GOV,Federal Agency - Executive,General Services Administration,Office of Citizen Services and Communications,Washington,DC,(blank)
DIGITAL.GOV,Federal Agency - Executive,General Services Administration,The General Services Administration,Washington,DC,(blank)
FEDRAMP.GOV,Federal Agency - Executive,General Services Administration,Office of Citizen Services and Innovative Technologies,Washington,DC,(blank)
ACQUISITION.GOV,Federal Agency - Executive,General Services Administration,Integrated Acquisition Environment,Arlington,VA,(blank)
CIO.GOV,Federal Agency - Executive,General Services Administration,Chief Information Officers Council,Washington,DC,(blank)
IDMANAGEMENT.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,(blank)
PERFORMANCE.GOV,Federal Agency - Executive,General Services Administration,GSA - Office of Citizen Services Innovative Technologies - OSCIT,Washington,DC,(blank)
SECTION508.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,(blank)
CPARS.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
FBO.GOV,Federal Agency - Executive,General Services Administration,GSA/CAO/OAS,Arlington,VA,(blank)
GSAADVANTAGE.GOV,Federal Agency - Executive,General Services Administration,US General Services Administration,Washington,DC,(blank)
GSAAUCTIONS.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,ITServiceDesk@gsa.gov
LOGIN.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Washington,DC,tts-vulnerability-reports@gsa.gov
SAM.GOV,Federal Agency - Executive,General Services Administration,General Services Administration,Arlington,VA,(blank)
EOF

# execute the scans
#./scan domains.csv --scan=200
./scan /tmp/domains.csv --scan=pshtt

# put scan results into s3
aws s3 cp cache/pshtt/ "s3://$BUCKET/" --recursive

# clean up old scans in s3

