#! /usr/bin/env python3
"""
API Test

This script gets a general level of reliability for Site-Scanner API. This
is done by testing the "/api/v1/date/{date}/domains/{domain}/{scantype}/" endpoint
with randomly choosen domains. It then shows output about success and error rates.

Args:
    api_url (str): The api url to test. Defaults to https://site-scanning.app.cloud.gov/
    api_version (str): The api version to test. Defaults to v1.
    num_domains (int): The number of domains to choose randomly. Defaults to 200.
    date (str): A date to test in the form YYYY-MM-DD. Defaults to yesterday's date.
    scan_types (str): A comma-separated list of scan types. Defaults to all scans.
"""

import asyncio
import csv
import dataclasses
import datetime
from collections import Counter
from itertools import islice, product
from random import SystemRandom
from typing import Any, List, Tuple
from urllib.parse import urljoin

import fire
import httpx

BASE_DOMAINS_URL = (
    "https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv"
)

client = httpx.AsyncClient(timeout=None)


@dataclasses.dataclass
class Request:
    """
    Request is an HTTP request.
    """

    url: str
    domain: str
    scantype: str


@dataclasses.dataclass
class Response:
    """
    Response is an HTTP response.
    """

    request: Request
    status: int
    content: str


async def get_domains() -> List[str]:
    """
    get_domains collects the base set of domains. This is the official GSA-managed
    list of federal domains without the subdomains from Censys.

    Returns:
    List[str] where "str" is the first column of the CSV.
    """
    csv_request = await client.get(BASE_DOMAINS_URL)
    domains_csv = csv_request.content.decode(
        "UTF-8"
    ).splitlines()  # TODO: probably a better way
    rows = csv.reader(domains_csv)
    domains = []
    for row in islice(rows, 1, None):  # skip csv header
        domains.append(row[0].lower())
    return domains


async def make_request(request: Request) -> Response:
    result = await client.get(request.url)
    response = Response(request, result.status_code, result.content)
    return response


async def test_api(requests: List[Request]) -> Tuple[Response]:
    results = await asyncio.gather(*[make_request(request) for request in requests])
    return results


def construct_requests(
    api_url: str, api_version: str, scantypes: List[str], date: str, domains: List[str]
) -> List[Request]:
    """
    construct_requests builds requests for the endpoint using scantypes, domains, and date.
    """

    requests = []
    for domain, scantype in product(domains, scantypes):
        endpoint = f"api/{api_version}/date/{date}/domains/{domain}/{scantype}/"
        url = urljoin(api_url, endpoint)
        request = Request(url, domain, scantype)
        requests.append(request)

    return requests


def random_list(num: int, list_: List[Any]) -> List[Any]:
    """
    random_list shuffles a list and returns the number of values specified by num.
    """
    cryptogen = SystemRandom()
    cryptogen.shuffle(list_)
    return list_[:num]


def process_responses(options: dict, responses: Tuple[Response]):
    """
    process_responses takes a tuple of Response objects and prints out the following:

    - success rate (number of requests - number of errors) / number of requests
    - error detail which shows the scantype and what percent of domains are affected by the error.
    """
    error_count = 0
    errors = []
    total_requests = options["num_domains"] * len(options["scan_types"])

    for response in responses:
        if response.status != 200:
            error_count += 1
            errors.append(response)

    success_rate = ((total_requests - error_count) / total_requests) * 100
    print(f"{total_requests} requests with {error_count} error(s)")
    print(f"Success rate: {success_rate}")

    if error_count:
        print("\nDisplaying errors...")
        counter = Counter()
        for error in errors:
            counter[error.request.scantype] += 1

        for k, v in counter.items():
            print(
                f"{v} errors for the {k} scantype. {(v / options['num_domains']) * 100}% of domains"
            )


async def main(options: dict):
    """
    main is the entry point function for the script.
    """
    print("Calculating baselines...")
    domains = await get_domains()
    random_domains = random_list(options["num_domains"], domains)
    requests = construct_requests(
        options["api_url"],
        options["api_version"],
        options["scan_types"],
        options["date"],
        random_domains,
    )
    responses = await test_api(requests)
    process_responses(options, responses)

    await client.aclose()
    return random_domains


def options(
    api_url: str = None,
    api_version: str = None,
    num_domains: int = None,
    date: str = None,
    scan_types: str = None,
) -> dict:
    if not api_url:
        api_url = "https://site-scanning.app.cloud.gov/"

    if not api_version:
        api_version = "v1"

    if not num_domains:
        num_domains = 200

    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")

    if scan_types:
        scans = scan_types.split(",")
    else:
        scans = [
            "pagedata",
            "200scanner",
            "uswds2",
            "sitemap",
            "privacy",
            "pshtt",
            "dap",
            "third_parties",
        ]

    opts = {
        "api_url": api_url,
        "api_version": api_version,
        "num_domains": num_domains,
        "date": date,
        "scan_types": scans,
    }

    return opts


options.__doc__ = __doc__


if __name__ == "__main__":
    opts = fire.Fire(options)
    result = asyncio.run(main(opts))
