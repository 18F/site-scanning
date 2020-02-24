#!/bin/sh
#
# This script fetches all the domains and splits them up into batches
# that can be used to parallelize the scanning across tasks.
#

# This is how many domains to scan in a single task
BATCHSIZE="${BATCHSIZE:-2000}"

# get the list of domains
if [ -f "$DOMAINCSV" ] ; then
	# this is so we can supply our own file for testing
	cp "$DOMAINCSV" /tmp/domains.csv
else
	wget -O /tmp/domains.csv https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv

	## If you add more domains (like subdomains), append them on to
	## /tmp/domains.csv in the https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv
	## format, so that when we load them in, we will be able to parse out
	## the agency, branch, etc.
	curl -s https://raw.githubusercontent.com/GSA/data/master/dotgov-websites/other-websites.csv | tail -n +2 | awk -F, '{printf("%s,,,,,,\n",$1)}' >> /tmp/domains.csv
fi


# figure out where to split the CSV up
if [ -n "$1" ] ; then
	SPLITDIR="$1"
else
	if [ -d "$TMPDIR" ] ; then
		SPLITDIR="$TMPDIR/splitdir"
	elif [ -d "/home/vcap/tmp/splitdir" ] ; then
		SPLITDIR="/home/vcap/tmp/splitdir"
	else
		SPLITDIR="/tmp/splitdir"
	fi
fi

# remove the header line from the CSV
tail -n +2 /tmp/domains.csv > /tmp/domains.txt

# split the CSV up!
echo splitting into "$SPLITDIR"
rm -rf "$SPLITDIR"
mkdir -p "$SPLITDIR"
cd "$SPLITDIR"
split -l "$BATCHSIZE" /tmp/domains.txt

# put the header line back into each file so that the CSV parser does the right thing
for i in $(ls "$SPLITDIR") ; do
	echo 'Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email' > "$i.csv"
	cat "$i" >> "$i.csv"
	rm "$i"
done

ls "$SPLITDIR"
