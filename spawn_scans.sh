#!/bin/sh
#
# This script takes split domains provided by getdomains.sh and spawns
# concurrent cloud.gov jobs for each.
#

TMPDIR="${TMPDIR:-/tmp}"
./getdomains.sh "$TMPDIR/splitdir"

# this tells cloud.gov to run the scan
# XXX This is assuming that the output of getdomains won't change
# XXX too much between when we run it here and when it runs on the
# XXX task nodes.  Probably a safe assumption, but there might be
# XXX a better way to do this.
for i in $(ls "$TMPDIR/splitdir") ; do
  cf run-task scanner-ui "/app/scan_engine.sh $i" --name "scan_engine $i" -m 1024M -k 4096M
  if [ "$?" != "0" ] ; then
    echo "running task on $i failed to work, pausing until previous jobs complete"
    NUMSCANS="$(cf tasks scanner-ui | grep RUNNING | wc -l)"
    until [ "$(cf tasks scanner-ui | grep RUNNING | wc -l)" != "$NUMSCANS" ] ; do
      echo "waiting until there's room to run $i"
      sleep 600
    done
    cf run-task scanner-ui "/app/scan_engine.sh $i" --name "scan_engine $i" -m 1024M -k 4096M
    if [ "$?" != "0" ] ; then
      FAILED="$i $FAILED"
      echo "$i task failed twice:  maybe we are out of memory?  Investigate!"
      echo "    trying the next task..."
    fi
  fi
done
if [ -n "$FAILED" ] ; then
  echo "summary of tasks that failed:  $FAILED"
  exit 1
fi
