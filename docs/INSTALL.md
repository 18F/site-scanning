# How to install Site Scanner

The site-scanner is engineered to run on cloud.gov using CircleCI for CI/CD.
You can also run a local copy if you want to do development on your laptop/desktop.
You should run these commands on a Mac OS X or Linux host which has tools such as cf, jq, curl, bash, etc on them.

**1. Create a cloud.gov account.**

- You can get a free non-production sandbox account by going to https://cloud.gov/quickstart/,
or by getting an IAA signed and then getting a real production cloud.gov org.
- Documentation on cloud.gov in general can be found here:  https://cloud.gov/docs/.
- Once you are set up and able to issue cloudfoundry commands like `cf target`, you will be able to proceed.

**2. Complete the initial setup.**

- Clone the site-scanner repo with `git clone https://github.com/18F/site-scanning`.
- `cd site-scanning` to get into the repo dir.
- Create the services required and do the initial app push:
	- If you are in a sandbox org/space, do this: `./deploy-cloudgov.sh setup`.
	- If you are in a production org/space, do this: `./deploy-cloudgov.sh setup prod`
  This will create the initial services in cloudfoundry, launch the scanner-ui app,
  and bind the services to the app.
- Run a scan to get some data with `cf run-task scanner-ui /app/scan_engine.sh`

You should now be able to go to the URLs given to you at the end of the deploy script
to see the UI/API in action.

**3. Get the CI/DC setup.**

- Fork the repo into your own github organization or into your github account, make sure that CircleCI is operating on this fork, and then configure a few environment variables into the CircleCI repo config.
- `CF_ORG`: This is your cf org.  You can get this with `cf target | grep org`.
- `CF_SPACE`:  This is your cf space.  You can get this with `cf target | grep space`.
- `CF_PASSWORD`:  This is the password that lets CircleCI deploy to your space.
	You can get it with `cf service-key scanner-ui deployer | grep password`
- `CF_USERNAME`:  This is the username that lets CircleCI deploy
	to your space.  You can get it with `cf service-key scanner-ui deployer | grep username`.

- Once these are set up, any time you push to master, it should run the tests and then
do a deploy if everything worked.  It will also start running scans once a day
automatically.
- The configuration for CircleCI can be found in `.circleci/config.yml`.

**4. Develop locally.**
Developing locally is a quick way to get up and going and test stuff out.
You will need to execute these steps for the next
few sections to work:

- [Install Docker](https://docs.docker.com/install/).
- Clone the site-scanner repo with `git clone https://github.com/18F/site-scanning`.
- `cd site-scanning` to get into the repo dir.

**5. Run tests.**

- Run `./test.sh` in your shell window that is in the repo dir.
- This can take a while, since the domain-scan repo is really giant, but it fires up
docker-compose so that it has all the required services and then runs all the python
tests (`./manage.py test`) as well as checking that a scan of a few domains works.
- For a faster test/development cycle, set up your python environment
and use the docker environment that test.sh sets up.  You can set up to do this by:
* Installing python 3, either through `brew install python3` or https://www.python.org/downloads/
* Running `python3 -m venv venv` inside the site-scanning directory.
* Running `. venv/bin/activate` inside the site-scanning directory.
* Running `pip3 install -r requirements.txt` inside the site-scanning directory.

- Once this environment is set up, to run the tests, you will need to:
* `. venv/bin/activate` to get python set up in your shell, if you haven't done this already.
* `./test.sh nodelete` to get the environment up and running in docker, if you haven't done this already.
* `./manage.py test` to run the tests.

- You can keep making changes to the code and running `./manage.py test` to quickly
test it against the small elasticsearch instance that is running in docker.
That instance has a few domains which are scanned and loaded in.  The list of
domains can be [found here](composetest.sh)).

**6. Run the app.**

- The simplest way to run the app locally with a populated test database is to
connect to the cloud.gov-deployed Elasticsearch database via an ssh tunnel:

```bash
cf7 connect-to-service scanner-ui scanner-es
```

If you have trouble making an ssh connection, you may need to use `cf7` and
manually configure the port forwarding. Get the hostname and ports from the
`connect-to-service` output, and run, replacing ports and hostname:

```bash
cf7 ssh -N -L 52046:hostname:32274 scanner-ui
```

- Set the `ESURL` environment variable to the provided port on localhost.

- Run `./manage.py runserver` to start the Django development server

Alternately, you may try to piggyback on the test runner's Docker-managed
database:

- Run `./test.sh nodelete` in the repo dir.  This will run the app, populate
it with data scanned from a few domains, run the test suite against it,
and leave the app running.

- You should then be able to go to http://localhost:8000/ and see the UI/API
working with whatever code was there when you ran the `test.sh` script.

- If you'd like to see the logs from the system, then type `docker-compose logs -f`,
and you will see the logs streamed from the app and the elasticsearch/minio
services.

**7. CI/CD into cloud.gov.**

- If you already have CI/CD going, you should be able to do development on a branch
and whenever you push your branch, it will run the tests.  You can see how that goes
in github if you have a PR for your branch, or by looking at CircleCI.

- If you want to do a deploy to production, you can merge your code into the master
branch, and it will do a test then deploy.

- Currently, there are stubs for being able to create a dev/staging/production deployment
setup, but this is unfinished as of now.

**8.Add scans.**

- Site Scanner uses the [domain-scan](https://github.com/18F/domain-scan) engine
to do the work of parallelizing and collecting all of the scan data. Documention exists to help you [add new scanners](https://github.com/18F/domain-scan#developing-new-scanners).

**9. Set up local development.**
- Check out the code:
```
git clone https://github.com/18F/domain-scan/
cd domain-scan
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
pip3 install -r requirements-scanners.txt
pip3 install -r requirements-gatherers.txt
pip3 install -r requirements-dev.txt
```

- You should now be able to run scans by hand as per the documentation:
```
./scan whitehouse.gov --scan=uswds2
```

- So long as you just create scans that scrape web pages or gather other
metadata directly, your scan should perform fine. Make sure the workers are bumped up to around 50.

- Copy the `domain-scan/scanners/uswds2.py` scanner plugin and use that as a template for your new scan, or the `domain-scan/scanners/200scanner.py` scanner.

**10. Test the new scans.**

- The primary test harness is the `./test.sh` script, which will fire
up an elasticsearch and S3 infrastructure, run a scan, load the data
into ES/S3, and then run the python `./manage.py test` command, as well
as do some other tests to make sure that S3 got populated.

- Note that a live scan is done on
18f.gov and gsa.gov. If they are down/offline or change how
they give data out, tests may start failing, and you may have to fix
that.

- Every commit will trigger a test run by CircleCI, which you should
be able to see the status of in Github.

- If you need further testing, there are a few scripts in this repo which
you might be able to look at in the `utilities` directory, like the `checkscanscores.sh`
script, which checks how well the uswds2 scanner works by checking the scores for
false positives and false negatives.

**11. Configure cloud.gov to use your branch.**

- Once you have developed your new scan type, you will need to check it into a branch
and try to get it PR'ed into the domain-scan repo.
- Until then, you will need to
configure your forked repo to use that branch, and to add your new scan type. To do this, edit the `site-scanning/scan_engine.sh` file and add another line
to the `SCANTYPES` definition near the top of the file for another scan, and
edit the `BRANCH` variable to set it to your branch.

**12. Kick off a cloud.gov scan for testing.**

- Once the code has made it into the master branch and the deploy to cloud.gov
has completed,
run `cf run-task scanner-ui /app/scan_engine.sh -m 1024M -k 4096M` to kick off a scan.
- You should be able to see how it goes with `cf logs scanner-ui`, and
once it completes, you should be able to see your scans in the API.
