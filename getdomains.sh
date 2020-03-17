#!/bin/sh
#
# This script fetches all the domains and splits them up into batches
# that can be used to parallelize the scanning across tasks.
#

# This is how many domains to scan in a single task
BATCHSIZE="${BATCHSIZE:-3000}"

BINDIR=$(dirname "$0")

# This function uses the mergedomaincsv.py script to ensure that
# there are no duplicate domains, and that the metadata from the first
# instance of a domain remains.
mergedomains() {
	"$BINDIR/mergedomaincsv.py" /tmp/domains.csv "$1" /tmp/mergeddomains.csv
	mv /tmp/mergeddomains.csv /tmp/domains.csv
}

# get the list of domains
if [ -f "$DOMAINCSV" ] ; then
	# this is so we can supply our own file for testing
	cp "$DOMAINCSV" /tmp/domains.csv
else
	# This is the base domain file with metadata in it already
	wget -O /tmp/domains.csv https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv

	# XXX HERE IS WHERE TO ADD MORE DOMAINS/SUBDOMAINS!!!
	# To add more files, make sure they are in the same format as the
	# current-federal.csv file, OR make sure that the domain is the first
	# field in your csv file.  You can put them in the domains dir, and
	# they will be merged in so there are no duplicates and metadata from
	# the first instance of the domain will be preserved.

	wget -O "$BINDIR/domains/other-websites.csv" https://raw.githubusercontent.com/GSA/data/master/dotgov-websites/other-websites.csv

	for i in $BINDIR/domains/*.csv ; do
		mergedomains "$i"
	done

	# clean up in case you are running this by hand and don't want to accidentally check this in
	rm -f "$BINDIR/domains/other-websites.csv"
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
rm -rf "$SPLITDIR"/*
mkdir -p "$SPLITDIR"
cd "$SPLITDIR"
split -l "$BATCHSIZE" /tmp/domains.txt

# put the header line back into each file so that the CSV parser does the right thing
for i in $(ls "$SPLITDIR") ; do
	echo 'Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email' > "$i.csv"
	cat "$i" >> "$i.csv"
	rm "$i"
done
