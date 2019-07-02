#!/bin/sh
#
# This script will check the scores for the uswds scan against some lists
# of domains which should or should not be USWDS-compliant, as documented in
# https://github.com/18F/site-scanning/issues/26
#
# It is meant to test the efficacy of the USWDS scanner, and runs on your
# local host.  You will need to have created a python venv for it, like so:
# 
# cd domain-scan
# python3 -m venv venv
# . venv/bin/activate
# pip install -r requirements.txt
# pip install -r requirements-scanners.txt
# pip install -r requirements-gatherers.txt
# pip install -r requirements-dev.txt
#

if [ ! -d domain-scan/venv ] ; then
	echo domain-scan/venv directory not found in "$(pwd)"
	exit 1
fi

export GOODDOMAINS=/tmp/gooddomains.$$.csv
cat <<EOF > "$GOODDOMAINS"
Domain Name
CitizenScience.gov
ClinicalTrials.gov
cbp.gov
cloud.gov
code.mil
commerce.gov
dds.mil
dhs.gov
dietaryguidelines.gov
dnfsb.gov
dol.gov
dotgov.gov
epa.gov
fca.gov
fcsic.gov
fec.gov
fedramp.gov
ffb.gov
floodsmart.gov
flra.gov
foia.gov
fpc.gov
gsa.gov
healthcare.gov
iawg.gov
imls.gov
irs.gov
itdashboard.gov
login.gov
manufacturing.gov
medicaid.gov
move.mil
mymedicare.gov
nih.gov
opioids.gov
pclob.gov
performance.gov
plainlanguage.gov
sba.gov
search.gov
stopbullying.gov
supremecourt.gov
treasury.gov
tsa.gov
unlocktalent.gov
usa.gov
usagm.gov
usaid.gov
usaid.gov
usajobs.gov
usaspending.gov
uscis.gov
uscourts.gov
usda.gov
usds.gov
usgs.gov
usich.gov
va.gov
vote.gov
whitehouse.gov
worker.gov
EOF

export BADDOMAINS=/tmp/baddomains.$$.csv
cat <<EOF > "$BADDOMAINS"
Domain Name
cdc.gov
census.gov
cpsc.gov
dea.gov
doi.gov
eeoc.gov
energy.gov
faa.gov
fbi.gov
fcc.gov
fda.gov
fdic.gov
federalreserve.gov
fema.gov
ftc.gov
fws.gov
gao.gov
nasa.gov
nps.gov
nsf.gov
osha.gov
secretservice.gov
ssa.gov
state.gov
transportation.gov
EOF

# activate the venv
cd domain-scan
. venv/bin/activate

# clean old scans up so that they do not confuse us
rm -f cache/uswds2/*.json

# scan good domains
./scan "$GOODDOMAINS" --scan=uswds2 >/dev/null 2>&1

# Output the score file from the scan results
rm -f /tmp/gooddomains_score.out
for i in cache/uswds2/*.json ; do
	jq -c '{total_score: .total_score, domain: .domain}' < "$i" >> /tmp/gooddomains_score.out
done

# report on how we did and clean up
echo "number of false negatives for the good domains:"
echo "  $(grep -c score..0, /tmp/gooddomains_score.out) out of $(grep -c . /tmp/gooddomains_score.out) ($(grep -c . "$GOODDOMAINS") - 1 checked)"
rm -f "$GOODDOMAINS"



# stash results so that the next scan is clean
mkdir -p /tmp/goodscans.$$
mv cache/uswds2/*.json /tmp/goodscans.$$

# scan bad domains
./scan "$BADDOMAINS" --scan=uswds2 >/dev/null 2>&1

# Output the score file from the scan results
rm -f /tmp/baddomains_score.out
for i in cache/uswds2/*.json ; do
	jq -c '{total_score: .total_score, domain: .domain}' < "$i" >> /tmp/baddomains_score.out
done

# report on how we did and clean up
echo "number of false positives for the bad domains:"
echo "  $(grep -cv score..0, /tmp/baddomains_score.out) out of $(grep -c . /tmp/baddomains_score.out) ($(grep -c . "$BADDOMAINS") - 1 checked)"
rm -f "$BADDOMAINS"

# restore good scans so that we end up with both sets for us to look at
mv /tmp/goodscans.$$/*.json cache/uswds2/
rmdir /tmp/goodscans.$$
