# How to manage Site Scanner as it is deployed in cloud.gov

## Deploying the app

The best way to deploy this app is with CI/CD.  This is currently set up to be done with [CircleCI](https://circleci.com/gh/18F/workflows/site-scanning).

1. The config for this is in `.circleci/config.yml`.
2. You can see the status of the builds/deploys by going to https://circleci.com/gh/18F/workflows/site-scanning .
3. CircleCI will run the `scan` job each night. This is what actually runs the scans and imports the results into Elasticsearch and the S3 bucket.

To run the scan manually
1. Delete today's scan:  If you do a new scan, you will have two scans in the index, and you'll
  get double results.  Follow the "Direct queries to Elasticsearch" section above to get
  you in, then delete that day's index using a command like `curl -k -X DELETE $ESURL/2019-07-29-*`,
  except with today's date.
2. Start the scan task:  Make sure you have the cf tools installed and you are authenticated
  and in the proper org/space, then run `cf run-task scanner-ui /app/scan_engine.sh -m 1024M`.
3. You can monitor the scan progress by watching `cf logs scanner-ui`.

## Restarting the app

1. [Set up the cf commandline tools](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line).
2. Log into this organization/space: `cf target -o gsa-10x-prototyping -s scanner_proto`.
3. Type `cf restart scanner-ui`.
4. The app should then restart.

## Getting to the app logs

If you need to do a basic search of the app logs, watch them streaming using the
[cf commandline tools](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line).

1. You can stream the logs directly once authenticated to cloud.gov and in the proper organization/space by saying `cf logs scanner-ui`.
2. As you do things on the site, you will see log messages streaming by.

OR

If you need to search further back than a few minutes or need to filter results or search for something in particulaur, use the cloud.gov [Kibana instance](https://logs.fr.cloud.gov/).

1. Go to https://logs.fr.cloud.gov/ and use their search interface to find what you need.
2. You can go to the [discover page](https://logs.fr.cloud.gov/app/kibana#/discover) and type in a query like `@cf.app:"scanner-ui" NOT "memory="` and then go hover over the `@message` field in the sidebar and select "Add" so that you only see the actual log message and the date.
3. Specify a time range in the upper right corner that is larger than the default of the last 15 minutes.
4. Type in words in quotes and tie them together with booleans like `AND`, `NOT`, etc. to find what you need.
5. You can read up further on [kibana query language](https://www.elastic.co/guide/en/elasticsearch/reference/6.8/query-dsl-query-string-query.html#query-string-syntax).

## Using debug mode

By default, debug mode is off.  Turning it on will allow people who get 500 error codes to see exceptions and other internal documentation. This is useful for debugging, but probably not for something that is exposed to the
public.

To turn on/off:
1. `cf set-env scanner-ui DEBUG True`.
2. `cf unset-env scanner-ui DEBUG`.
3. Restart the app with `cf restart scanner-ui`.

When debugging:
1. Make sure you have the [cf commandline tools](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line)
set up and authenticated, and you are in the proper organization/space.
2. Type `cf ssh scanner-ui`.
3. You should soon have a prompt inside the instance that is running the app.

## Making direct queries to Elasticsearch

You can use curl to query Elasticsearch either on the cloud.gov host, or locally with port-forwarding.

### Connect to Elasticsearch

#### On the cloud.gov host

1. ssh into a `scanner-ui` instance (see directly above).
2. Type `export ESURL=$(echo "$VCAP_SERVICES" | jq -r '.elasticsearch56[0].credentials.uri')`. This will make sure that you will have the credentials/config required to query ES.

#### Locally

To port-forward ssh to localhost, you can use the `cf connect-to-service` command. Note that at time of writing, `cf7` is required:

```bash
cf7 connect-to-service scanner-ui scanner-es
```

If you have trouble making an ssh connection, you may need to use `cf7` and manually configure the port forwarding. Get the hostname and ports from cloud.gov, and run, replacing ports and hostname:

```bash
cf7 ssh -N -L 52046:hostname:32274 scanner-ui
```

- Set the `ESURL` environment variable to the provided port on localhost.

### Querying Elasticsearch

Once connected, you should be able to query Elasticsearch with commands like this:

* `curl -s $ESURL/_cat/indices?v`
* `curl -k -X DELETE $ESURL/2019-07-29-pagedata` (deletes indexes)
* `curl -k -X DELETE $ESURL/2019-07-29-*` (deletes indexes)

You can read up further on [Elasticsearch query language](https://www.elastic.co/guide/en/elasticsearch/reference/5.5/_introducing_the_query_language.html).
