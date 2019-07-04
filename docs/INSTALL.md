# Installation Instructions

The site-scanner is engineered to run on cloud.gov using CircleCI for CI/CD.
You can also run a local copy if you want to do development on your laptop/desktop.

## Bootstrapping into cloud.gov

If you want to get the site-scanner going, you will first need to get a cloud.gov account.
You can get a free non-production sandbox account by going to https://cloud.gov/quickstart/,
or by getting an IAA signed and then getting a real production cloud.gov org.  Documentation
on cloud.gov in general can be found here:  https://cloud.gov/docs/.  Once you are set up
and able to issue cloudfoundry commands like `cf target`, you will be able to proceed.

### Initial Setup

We are assuming that you are running these commands on a Mac OS X or Linux host
which has tools such as cf, jq, curl, bash, etc on them.

- Clone the site-scanner repo with `git clone https://github.com/18F/site-scanning`.
- `cd site-scanning` to get into the repo dir.
- Create the services required and do the initial app push:
	- If you are in a sandbox org/space, do this: `./deploy-cloudgov.sh setup`.
	- If you are in a production org/space, do this: `./deploy-cloudgov.sh setup prod`
  This will create the initial services in cloudfoundry, launch the scanner-ui app,
  and bind the services to the app.
- Run a scan to get some data with `cf run-task scanner-ui /app/scan_engine.sh`

You should now be able to go to the URLs given to you at the end of the deploy script
to see the API in action.

### CI/CD Config

If you want to get CI/CD going, you will want to fork the repo into your own github
org or into your github account, make sure that CircleCI is operating on this fork,
and then configure a few environment variables into the CircleCI repo config.
- `AWS_ACCESS_KEY_ID`:  This is the key ID that can be used to access the S3 bucket.
	It is needed so tests can be run in CircleCI.  You can get it with the following command:
	`cf env scanner-ui | grep access_key_id`.
- `AWS_DEFAULT_REGION`:  This is the region your S3 bucket is in.  You can get it with
	`cf env scanner-ui | grep region`.
- `AWS_SECRET_ACCESS_KEY`:  This is the secret key for the S3 bucket.  You can get it
	with `cf env scanner-ui | grep secret_access_key`.
- `BUCKETNAME`:  This is the name of the S3 bucket.  You can get it with
	`cf env scanner-ui | grep bucket`.
- `CF_ORG`: This is your cf org.  You can get this with `cf target | grep org`.
- `CF_SPACE`:  This is your cf space.  You can get this with `cf target | grep space`.
- `CF_PASSWORD`:  This is the password that lets CircleCI deploy to your space.
	You can get it with `cf service-key scanner-ui deployer | grep password`
- `CF_USERNAME`:  This is the username that lets CircleCI deploy
	to your space.  You can get it with `cf service-key scanner-ui deployer | grep username`.

Once these are set up, any time you push to master, it should run the tests and then
do a deploy if everything worked.  It will also start running scans once a day
automatically.

The configuration for CircleCI can be found in `.circleci/config.yml`.

## Development Cycle


### Local Development

Developing locally is a quick way to get up and going and test stuff out.  

#### Set up venv
Make sure you are in the site-scanning repo directory, then set up a python
virtual env for you to work in and make sure you have all the python libs:
```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

#### Configure where S3 bucket lives

You will need to supply some infrastructure to make the app work.  You will either
need to point the app at the S3 bucket that is in cloud.gov, or set up your own
S3 bucket and fill it with scans for it to look at.

##### Using cloud.gov S3 bucket
If you want to point your API at the data that is in cloud.gov, you will need to
set environment variables to point at it with `export VARIABLE=XXX` in your shell.
These are the variables you must set:
- `AWS_ACCESS_KEY_ID`:  This is the key ID that can be used to access the S3 bucket.
	It is needed so tests can be run in CircleCI.  You can get it with the following command:
	`cf env scanner-ui | grep access_key_id`.
- `AWS_DEFAULT_REGION`:  This is the region your S3 bucket is in.  You can get it with
	`cf env scanner-ui | grep region`.
- `AWS_SECRET_ACCESS_KEY`:  This is the secret key for the S3 bucket.  You can get it
	with `cf env scanner-ui | grep secret_access_key`.
- `BUCKETNAME`:  This is the name of the S3 bucket.  You can get it with
	`cf env scanner-ui | grep bucket`.

##### Using your own S3 bucket
You will need to create your own S3 bucket somewhere and either create a role account,
or use your own credentials.  Again, use `export VARIABLE=XXX` in your shell to
set these variables.
- `AWS_ACCESS_KEY_ID`:  This is the key ID that can be used to access the S3 bucket.
- `AWS_DEFAULT_REGION`:  This is the region your S3 bucket is in.
- `AWS_SECRET_ACCESS_KEY`:  This is the secret key for the S3 bucket.
- `BUCKETNAME`:  This is the name of the S3 bucket.

If you have just created the bucket and need to fill it with data, download and follow
the directions on https://github.com/18F/domain-scan to install the scanner and run
a scan.  Once you have some scan data on a few domains, you can copy them to your s3
bucket with something like `aws s3 cp cache/pshtt/ "s3://$BUCKETNAME/pshtt/" --recursive`,
if you did a pshtt scan, for example.

#### Run tests

`./manage.py test`

#### Run the app

`./manage.py runserver`

You should then be able to go to http://127.0.0.1:8000/api/v1/scans/ and see the API
working.


### CI/CD into cloud.gov

If you already have CI/CD going, you should be able to do development on a branch
and whenever you push your branch, it will run the tests.  You can see how that goes
in github if you have a PR for your branch, or by looking at CircleCI.

If you want to do a deploy to production, you can merge your code into the master
branch, and it will do a test then deploy.

Currently, there are stubs for being able to create a dev/staging/production deployment
setup, but this is unfinished as of now.

## Adding Scans

The site-scanning project uses the [domain-scan](https://github.com/18F/domain-scan) engine
to do the work of parallelizing and collecting all of the scan data.  There is a good
section on how to [add new scanners](https://github.com/18F/domain-scan#developing-new-scanners)
which is excellent, but there are a few things that you might want to know about how to
develop and test these things.

### Set Up Local Development

Check out the code: 
```
git clone https://github.com/18F/domain-scan/
cd domain-scan
# Temporary until https://github.com/18F/domain-scan/pull/307 is merged
git checkout tspencer/200scanner
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-scanners.txt
pip install -r requirements-gatherers.txt
pip install -r requirements-dev.txt
```

You should now be able to run scans by hand as per the documentation:
```
./scan whitehouse.gov --scan=uswds2
```

So long as you just create scans that scrape web pages or gather other
metadata directly, your scan should perform fine.  I would recommend that you
make sure the workers are bumped up to 50 or something like that.

A good thing to do is to copy the `domain-scan/scanners/uswds2.py` scanner
plugin and use that as a template for your new scan.
Either that or the `domain-scan/scanners/200.py` scanner.

### Testing

The scanner will output it's scan data into `domain-scan/cache/<scantype>/*.json`.
These json files will be copied into the s3 bucket by the scanning engine, so
make sure they have good data.

If you need further testing, there are a few scripts in this repo which
you might be able to look at in the `utilities` directory, like the `checkscanscores.sh`
script, which checks how well the uswds2 scanner works by checking the scores for
false positives and false negatives.

### Configuring cloud.gov to use your branch

Once you have developed your new scan type, you will need to check it into a branch
and try to get it PR'ed into the domain-scan repo.  Until then, you will need to
configure your forked repo to use that branch, and to add your new scan type.

To do this, edit the `site-scanning/scan_engine.sh` file and add another line
to the `SCANTYPES` definition near the top of the file for another scan, and
edit the `BRANCH` variable to set it to your branch.

### Kick off a cloud.gov scan for testing

Once the code has made it into the master branch and the deploy to cloud.gov
has completed,
run `cf run-task scanner-ui /app/scan_engine.sh` to kick off a scan.
You should be able to see how it goes with `cf logs scanner-ui`, and
once it completes, you should be able to see your scans in the API.
