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

if [ "$1" = "setup" ] ; then  echo
	# create services (if needed)
	if service_exists "scanner-storage" ; then
	  echo scanner-storage already created
	else
	  if [ "$2" = "prod" ] ; then
	    cf create-service s3 basic-public scanner-storage
	  else
	    cf create-service s3 basic-public-sandbox scanner-storage
	  fi
	fi

	if service_exists "scanner-ui-deployer" ; then
	  echo scanner-ui-deployer already created
	else
	  cf create-service cloud-gov-service-account space-deployer scanner-ui
	  cf create-service-key scanner-ui deployer
	  echo "to get the CF_USERNAME and CF_PASSWORD, execute 'cf service-key scanner-ui deployer'"
	fi
fi

# launch the app
cf push

# tell people where to go
ROUTE="$(cf apps | grep scanner-ui | awk '{print $6}')"
echo
echo
echo "to log into the site, you will want to go to https://${ROUTE}/api/v1/scans/ or https://${ROUTE}/api/v1/domains/"
echo "Have fun!"

