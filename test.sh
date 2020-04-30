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
echo waiting until "$CONTAINER" is running
until docker ps -f name="$CONTAINER" -f status=running | grep scanner-ui ; do
	docker ps
	sleep 2
done

# Run the test!
docker exec "$CONTAINER" ./composetest.sh
SAVEDEXIT=$?

# # do an OWASP ZAP scan XXX this takes too long
# docker exec "$CONTAINER" ./manage.py migrate
# export ZAP_CONFIG=" \
#   -config globalexcludeurl.url_list.url\(0\).regex='.*/robots\.txt.*' \
#   -config globalexcludeurl.url_list.url\(0\).description='Exclude robots.txt' \
#   -config globalexcludeurl.url_list.url\(0\).enabled=true \
#   -config spider.postform=true"
# CONTAINER=$(docker-compose images | awk '/zaproxy/ {print $1}')
# echo "====================================== OWASP ZAP tests"
# docker exec "$CONTAINER" zap-full-scan.py -t http://scanner-ui:8000/about/ -m 5 -z "${ZAP_CONFIG}" | tee /tmp/zap.out
# if grep 'FAIL-NEW: 0' /tmp/zap.out >/dev/null ; then
# 	echo 'passed OWASP ZAP'
# else
# 	ecgi 'OWASP ZAP scan failed'
# 	SAVEDEXIT=1
# fi

# clean up (if desired)
if [ "$1" != "nodelete" ] ; then
	docker-compose down
fi

exit "$SAVEDEXIT"
