# Architecture

There are three components to this project:
- *The Scanning Engine:*  This engine, when executed, will run all the configured scans 
  against all of the configured domains and generate json output.
- *Scanning Engine Plugins:*  These will be plugins that will let you execute different
  types of scans.  They will be used by the scanning engine, or can be executed by hand.
  It is anticipated that over time, more plugins will be created to expand the functionality
  of the scanning engine.
- *Scan Result UI:*  This is a web frontend that implements a REST API to download/search
  scan results.


## Continuous Deployment

The components are deployed using CircleCI into cloud.gov and once a day, the scanning engine is
executed using https://docs.cloudfoundry.org/devguide/using-tasks.html#run-tasks, generating
it's json files into S3.  The UI then can be used to find and download the scan results.


## Scan API

The scan API map is:
  - `/api/v1/domains/` pulls down all of the scan results for all domains.
  - `/api/v1/domains/{domain}` pulls down all of the scan results for a particular domain.
  - `/api/v1/scans/` pulls down all of the scan results for all scantypes.
  - `/api/v1/scans/{scantype}` pulls down all of the scan results for all domains that have this scantype.

The API returns data about the scans that we have, as well as a reference to where the scans are actually
stored.  For example:
```
$ curl -s https://APPNAME.app.cloud.gov/api/v1/domains/18f.gov/ | jq -r .
[
  {
    "domain": "18f.gov",
    "scantype": "200",
    "scan_data_url": "https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/18f.gov.json",
    "lastmodified": "2019-07-01T20:58:41Z"
  }
]
$ curl -s https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/18f.gov.json | jq -r .
{
  "/": "200",
  "/code.json": "404",
  "/data": "404",
  "/data.json": "404",
  "/developer": "200",
  "/digitalstrategy/": "404",
  "/open": "404",
  "/privacy": "404",
  "/robots.txt": "200",
  "/sitemap.xml": "200"
}
$
```

## Scan Data Storage

The scans are stored on disk as json files named by the domain and placed in a scantype
subdirectory in a public S3 bucket.  The location of the files can be found by querying
the API, like so:
```
$ curl -s https://APPNAME.app.cloud.gov/api/v1/scans/ | jq -r '.[] | .scan_data_url'
https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/18f.gov.json
https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/2020census.gov.json
https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/9-11commission.gov.json
https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/911.gov.json
https://s3-us-gov-west-1.amazonaws.com/BUCKETNAME/200/911commission.gov.json
...
$ 
```
