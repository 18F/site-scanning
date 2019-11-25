# DevOps!

This is where you can learn how to manage the site-scanner app as it is deployed in
cloud.gov.

## Restarting

To restart the app, you will need to [set up the cf commandline tools](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line).

Once you have installed everything and logged in, get into the proper org/space: `cf target -o gsa-10x-prototyping -s scanner_proto`

Then, type `cf restart scanner-ui`.

The app should then restart.

## Logs

To get to the logs, you can either watch them streaming using the
[cf commandline tools](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line),
or you can use the cloud.gov [Kibana instance](https://logs.fr.cloud.gov/).

### cf commandline tools

You can stream the logs directly once authenticated to cloud.gov and in the proper org/space
by saying `cf logs scanner-ui`.  As you do things on the site, you will see log messages
streaming by.

### cloud.gov Kibana

The cf tools can go back in time a bit, but if you need to search further back than a few
minutes or need to filter the results or search for something in particular, you can use
the cloud.gov Kibana instance to do this.  Just go to https://logs.fr.cloud.gov/ and use
their search interface to find what you need.

I usually go to the [discover page](https://logs.fr.cloud.gov/app/kibana#/discover) and
type in a query like `@cf.app:"scanner-ui" NOT "memory="` and then go hover over the
`@message` field in the sidebar and select "Add" so that I only see the actual log message
and the date.  You may have to specify a time range in the upper right corner that is larger
than the default of the last 15 minutes.

The [kibana query language](https://www.elastic.co/guide/en/elasticsearch/reference/6.8/query-dsl-query-string-query.html#query-string-syntax)
is super flexible and too big to document here.  But you can usually type in words in
quotes and tie them together with booleans like `AND`, `NOT`, etc. to find what you
need.

## Debug Mode

By default, debug mode is off, which is proper for production.  If you turn this on,
people who get 500 error codes can see the exceptions and all sorts of internal stuff.
This is useful for debugging, but probably not for something that is exposed to the
public.

You can turn this on/off by saying:
* `cf set-env scanner-ui DEBUG True`
* `cf unset-env scanner-ui DEBUG`

And then restarting the app with `cf restart scanner-ui`.

## CI/CD

The best way for you to deploy this app is with CI/CD.  This is currently
set up to be done with [CircleCI](https://circleci.com/gh/18F/workflows/site-scanning).

The config for this is in `.circleci/config.yml`.  You can see the status of the
builds/deploys by going to https://circleci.com/gh/18F/workflows/site-scanning .

One thing to note is that during the night, CircleCI will run the `scan` job.
This is what actually runs the scans and imports the results into Elasticsearch
and the S3 bucket.  If you feel the need to run the scan manually for some reason,
be sure to consult the "Running a scan by hand" section of this document.

## ssh into the scanner

If you would like to get into the site-scanner node to do some debugging, make sure you
have the [cf commandline tools](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line)
set up and authenticated, and you are in the proper org/space.

Then, type `cf ssh scanner-ui`.  You should soon have a prompt inside the instance that is
running the app.

## Direct queries to Elasticsearch

If you would like to do direct queries to elasticsearch, you will first need to ssh
into a `scanner-ui` instance, as documented above.  Then, type
`export ESURL=$(echo "$VCAP_SERVICES" | jq -r '.elasticsearch56[0].credentials.uri')`.
This will make sure that you will have the credentials/config required to query ES.

You then should be able to query Elasticsearch with commands like this:
* `curl -s $ESURL/_cat/indices?v`
* `curl -k -X DELETE $ESURL/2019-07-29-pagedata`
* `curl -k -X DELETE $ESURL/2019-07-29-*`

The second two commands delete indexes, which is something that you might not want to do
unless you want to run another scan by hand or something.  You should
consult the [Elasticsearch query language documentation](https://www.elastic.co/guide/en/elasticsearch/reference/5.5/_introducing_the_query_language.html)
to understand everything you can do.


## Running a scan by hand

If, for some reason, there is a desire to re-run a scan or something like that, you will
need to:
* Delete today's scan:  If you do a new scan, you will have two scans in the index, and you'll
  get double results.  Follow the "Direct queries to Elasticsearch" section above to get
  you in, then delete that day's index using a command like `curl -k -X DELETE $ESURL/2019-07-29-*`,
  except with today's date.
* Start the scan task:  Make sure you have the cf tools installed and you are authenticated
  and in the proper org/space, then run `cf run-task scanner-ui /app/scan_engine.sh -m 1024M`.
* You can monitor the scan progress by watching `cf logs scanner-ui`.
