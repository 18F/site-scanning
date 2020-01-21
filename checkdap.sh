#!/bin/sh
#
# This script will check whether the DAP queries are accurate
# using phantomjs to pull down the full page.
#

if command -v phantomjs >/dev/null ; then
	echo "good, phantomjs is installed"
else
	echo "error:  phantomjs needs to be installed for this to work"
	exit 1
fi

if [ -f "$1" ] ; then
	DAPJSON="$1"
else
	DAPJSON="/tmp/dap-$$.json"
	curl https://site-scanning.app.cloud.gov/api/v1/scans/dap/ > "$DAPJSON" 2>/dev/null
fi

cat <<EOF > "/tmp/save_page-$$.js"
var system = require('system');
var page = require('webpage').create();

page.open(system.args[1], function()
{
    console.log(page.content);
    phantom.exit();
});
EOF

jq -rj '.[] | .domain, " ", .data.dap_detected, "\n"' "$DAPJSON" | while read line ; do
	set $line
	echo " # doing $1 which is $2"
	phantomjs "/tmp/save_page-$$.js" https://"$1" > /tmp/page.$$.html

	if grep -E "UA-33523145-1|dap.digitalgov.gov/Universal-Federated-Analytics-Min.js|_fed_an_ua_tag" /tmp/page.$$.html >/dev/null ; then
		if [ "$2" != "true" ] ; then
			echo "$1 is a false negative (should be true)"
		fi
	else
		if [ "$2" != "false" ] ; then
			echo "$1 is a false positive (should be false)"
		fi
	fi
done

rm -f "/tmp/dap-$$.json"
rm -f "/tmp/save_page-$$.js"

