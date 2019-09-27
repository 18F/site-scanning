#!/bin/sh
# 
# This script configures environment variables, starts up a local test environment,
# and then runs tests.
#

# set env vars
AWS_ACCESS_KEY_ID=$(date +%s | sha256sum | base64 | head -c 20)
AWS_SECRET_ACCESS_KEY=$(date +%s | sha256sum | base64 | head -c 40)
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION="us-east-1"
export BUCKETNAME="data"
export S3ENDPOINT="--endpoint-url=http://localhost:9000"
export ESURL="http://localhost:9200"
export DOMAINCSV="/tmp/testdomains.csv"

# start up elasticsearch
docker pull docker.elastic.co/elasticsearch/elasticsearch:5.6.16
docker run -d --name=scanner-es -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" \
	-e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:5.6.16

# start up minio (s3)
docker pull minio/minio
docker run -d --name=scanner-storage -p 9000:9000 \
	-e "MINIO_ACCESS_KEY=$AWS_ACCESS_KEY_ID" \
	-e "MINIO_SECRET_KEY=$AWS_SECRET_ACCESS_KEY" \
	minio/minio server /data

# make sure these services have a little time to get going
sleep 2

# function to give us a way to exit early and clean up if need be.
cleanup()
{
	echo stopping docker services
	docker stop scanner-es
	docker rm scanner-es
	docker stop scanner-storage
	docker rm scanner-storage

	if [ -z "$1" ] ; then
		exit 0
	else
		echo "failed: $1"
		docker ps
		exit 1
	fi
}

# set up environment
if [ ! -d venv ] ; then
	python3 -m venv venv
fi
. venv/bin/activate
pip install -r requirements.txt
aws $S3ENDPOINT s3 mb s3://"$BUCKETNAME" || cleanup "could not create s3 bucket"
./manage.py migrate || cleanup "could not do db migrations"

# load data into our environment
cat <<EOF > "$DOMAINCSV"
Domain Name,Domain Type,Agency,Organization,City,State,Security Contact Email
18F.GOV,Federal Agency - Executive,General Services Administration,18F,Washington,DC,tts-vulnerability-reports@gsa.gov
GSA.GOV,Federal Agency - Executive,General Services Administration,GSA,Washington,DC,(blank)
EOF
./scan_engine.sh "$BUCKETNAME"


# run app test suite
./manage.py test || cleanup "python test suite exited uncleanly"

# do a test that checks if the s3 bucket contains data
echo "checking what is in the s3 bucket"
aws $S3ENDPOINT s3 ls "s3://$BUCKETNAME/privacy/" | grep 18f.gov >/dev/null || cleanup "s3 bucket does not contain a selected scan"

# test that there are indexes available
echo "checking whether indexes were created"
curl -s "$ESURL"/_cat/indices?v | grep pagedata >/dev/null || cleanup "the pagedata index was not created"

# everything must be great!
cleanup
