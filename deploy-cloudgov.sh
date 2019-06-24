#!/bin/sh
#
# This script will attempt to create the services required
# and then launch everything.
#

# function to check if a service exists
service_exists()
{
  cf service "$1" >/dev/null 2>&1
}

# create services (if needed)
if service_exists "scanner-storage" ; then
  echo scanner-storage already created
else
  if [ "$1" = "prod" ] ; then
    cf create-service s3 basic scanner-storage
  else
    cf create-service s3 basic-sandbox scanner-storage
  fi
fi

# launch the app
cf push

# tell people where to go
ROUTE=$(cf apps | grep scanner-ui | awk '{print $6}')
echo
echo
echo "  to log into the site, you will want to go to https://${ROUTE}/"
echo "  Have fun!"

