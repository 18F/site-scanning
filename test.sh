#!/bin/sh
#
# This is what sets up and actually runs the test
#
# You can run it like ./test.sh nodelete to leave the test env running
#

# Set some secrets up
export MINIO_SECRET_KEY=$(date +%s | sha256sum | base64 | head -c 40)
export MINIO_ACCESS_KEY=$(date +%s | sha256sum | base64 | head -c 20)

# Start the docker stuff up with a fresh env
docker-compose down
docker-compose up -d --build

# Make sure everything has time to awaken
sleep 10

# Run the test!
docker exec site-scanning_scanner-ui_1 ./composetest.sh
SAVEDEXIT=$?

# clean up (if desired)
if [ "$1" != "nodelete" ] ; then
	docker-compose down
fi

exit "$SAVEDEXIT"
