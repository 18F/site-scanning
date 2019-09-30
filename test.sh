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


# find the container name:
CONTAINER=$(docker-compose images | awk '/scanner-ui/ {print $1}')

# Wait until it is running
until docker ps -f name="$CONTAINER" -f status=running | grep scanner-ui ; do
	sleep 1
done

# Run the test!
docker exec "$CONTAINER" ./composetest.sh
SAVEDEXIT=$?

# clean up (if desired)
if [ "$1" != "nodelete" ] ; then
	docker-compose down
fi

exit "$SAVEDEXIT"
