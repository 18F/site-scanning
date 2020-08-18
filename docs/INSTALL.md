# Setup Spotlight

Spotlight is engineered to run on cloud.gov using CircleCI for CI/CD.
You can also run a local copy for local development. 
You should run these commands on a Mac OS X or Linux host which has tools such as cf, jq, curl, bash, etc on them.

## Cloud.gov Setup

### Create a cloud.gov account
- You can get a free non-production sandbox account by going to https://cloud.gov/quickstart/,
or by getting an IAA signed and then getting a real production cloud.gov org.
- Documentation on cloud.gov in general can be found here:  https://cloud.gov/docs/.
- Once you are set up and able to issue cloudfoundry commands like `cf target`, you will be able to proceed.

### Complete the initial setup
- Clone the repo with `git clone https://github.com/18F/Spotlight` or `git clone git@github.com:18F/Spotlight.git` over SSH.

- `cd Spotlight` to get into the repo dir.
- Create the services required and do the initial app push:
	- If you are in a sandbox org/space, do this: `./deploy-cloudgov.sh setup`.
	- If you are in a production org/space, do this: `./deploy-cloudgov.sh setup prod`
  This will create the initial services in cloudfoundry, launch the scanner-ui app,
  and bind the services to the app.
- Run a scan to get some data with `cf run-task scanner-ui /app/scan_engine.sh`

You should now be able to go to the URLs given to you at the end of the deploy script
to see the UI/API in action.

### CI/CD setup
- Fork the repo into your own github organization or into your github account, make sure that CircleCI is operating on this fork, and then configure a few environment variables into the CircleCI repo config.
- `CF_ORG`: This is your cf org.  You can get this with `cf target | grep org`.
- `CF_SPACE`:  This is your cf space.  You can get this with `cf target | grep space`.
- `CF_PASSWORD`:  This is the password that lets CircleCI deploy to your space.
	You can get it with `cf service-key scanner-ui deployer | grep password`
- `CF_USERNAME`:  This is the username that lets CircleCI deploy
	to your space.  You can get it with `cf service-key scanner-ui deployer | grep username`.

- Once these are set up, any time you push to `main`, it should run the tests and then
do a deploy if everything worked.  It will also start running scans once a day
automatically.
- The configuration for CircleCI can be found in `.circleci/config.yml`.

- You can test the CircleCI configuration locally as well. 
	- Install the [CircleCI Local CLI tools](https://circleci.com/docs/2.0/local-cli/#installation). On Mac OS X you can install with `brew install circleci`.
	- Be sure to run the `circleci setup` step.
	- Validate the config with `circleci config validate`.
	- You can run any of the jobs locally if you have Docker installed.
		- For example, to run the `build` job you would run `circleci local execute --job build`

## Development Setup

Spotlight requires Docker and Python to run locally.

### Code
- Clone the repo with `git clone https://github.com/18F/Spotlight` or `git clone git@github.com:18F/Spotlight.git` over SSH.
- `cd Spotlight` to get into the repo dir.

### Docker
- [Install Docker](https://docs.docker.com/install/).
- Run `docker --version` and `docker-compose --version` to ensure that both are installed.
- To set up the environment with no data run `docker-compose up --build -d`
- To set up the environment with data, see the (Run Tests)[#run-tests] section
- Troubleshooting: Docker for Mac's default memory requirements are not sufficient to run ElasticSearch. If you're having trouble getting the ElasticSearch container to start or if you're seeing Exit Code 137, open up the Docker Preferences and set the memory to at least 4 GB.

### Python

#### pyenv
While optional, we recommend that you use `pyenv` to manage your Python versions. 
- [Install pyenv](https://github.com/pyenv/pyenv#homebrew-on-macos)
- `cd` into the repo and run `pyenv install` to install the project's Python version.

#### Poetry
- [Install Poetry](https://github.com/python-poetry/poetry#installation). Poetry is a sophisticated Python dependency manager that has manages virtual environemnts, supports deterministic builds, and has a dependency solver.

- [Install Poetry](https://github.com/python-poetry/poetry#installation)
- Install the project's dependencies with `poetry install`. 
- There are two ways to run scripts with Poetry:
	- `poetry shell` creates a shell with the virtual environment in which you can run 
	- `poetry run <command>` runs the command inside the virtual environment without creating a shell.

### VS Code
Optional. Using VS Code to run the dev dependencies `bandit`, `black`, `pylint`, and `flake8` on save.

### Run Tests

- Run `./test.sh` in your shell window that is in the repo dir.
- This can take a while, since the domain-scan repo is really giant, but it fires up
docker-compose so that it has all the required services and then runs all the python
tests (`./manage.py test`) as well as checking that a scan of a few domains works.
- For a faster test/development cycle, set up your python environment
and use the docker environment that test.sh sets up.  You can set up to do this by:

* `./test.sh nodelete` to get the environment up and running in docker, if you haven't done this already.
* `poetry run python manage.py test` to run the tests.

- You can keep making changes to the code and running `poetry run manage.py test` to quickly
test it against the small elasticsearch instance that is running in docker.
That instance has a few domains which are scanned and loaded in.  The list of
domains can be [found here](composetest.sh)).

### Running Locally Against Cloud.gov
- One simple way to run the app locally with a populated test database is to
connect to the cloud.gov-deployed Elasticsearch database via an ssh tunnel.

- See [the DevOps documentation](Devops.md#connect-to-elasticsearch) for details on how to tunnel from cloud.gov
- Set the `ESURL` environment variable to the provided port on localhost.
- Run `poetry run python manage.py runserver` to start the Django development server

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

### CI/CD into cloud.gov

- If you already have CI/CD going, you should be able to do development on a branch
and whenever you push your branch, it will run the tests.  You can see how that goes
in github if you have a PR for your branch, or by looking at CircleCI.

- If you want to do a deploy to production, you can merge your code into the `main`
branch, and it will do a test then deploy.

- Currently, there are stubs for being able to create a dev/staging/production deployment
setup, but this is unfinished as of now.

### Domain Scan
- Spotlight uses the [domain-scan](https://github.com/18F/domain-scan) engine
to do the work of parallelizing and collecting all of the scan data. Documention exists to help you [add new scanners](https://github.com/18F/domain-scan#developing-new-scanners).

#### Set up local development
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

#### Test the new scans

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

#### Configure cloud.gov to use your branch

- Once you have developed your new scan type, you will need to check it into a branch
and try to get it PR'ed into the domain-scan repo.
- Until then, you will need to
configure your forked repo to use that branch, and to add your new scan type. To do this, edit the `site-scanning/scan_engine.sh` file and add another line
to the `SCANTYPES` definition near the top of the file for another scan, and
edit the `BRANCH` variable to set it to your branch.

#### Kick off a cloud.gov scan for testing

- Once the code has made it into the `main` branch and the deploy to cloud.gov
has completed,
run `cf run-task scanner-ui /app/scan_engine.sh -m 1024M -k 4096M` to kick off a scan.
- You should be able to see how it goes with `cf logs scanner-ui`, and
once it completes, you should be able to see your scans in the API.
