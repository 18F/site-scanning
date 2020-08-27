#! /usr/bin/env python3
"""Baseline API Tester

python baseline.py

This script attempts to get a general level of reliability for the API. This
is done by testing the "/api/v1/date/{date}/domains/{domain}/{scantype}/" endpoint
with n randomly choosen domains.
"""

import asyncio
import csv
import dataclasses
import datetime
from collections import Counter
from itertools import islice, product
from random import SystemRandom
from typing import Any, List, Union, Tuple
from urllib.parse import urljoin

import httpx

API_URL = "https://site-scanning.app.cloud.gov/"
API_VERSION = "v1"
NUM_DOMAINS = 200
SCAN_TYPES = [
    "pagedata",
    "200scanner",
    "uswds2",
    "sitemap",
    "privacy",
    "dap",
    "third_parties",
    "pshtt",
]
BASE_DOMAINS_URL = (
    "https://github.com/GSA/data/raw/master/dotgov-domains/current-federal.csv"
)

client = httpx.AsyncClient()


@dataclasses.dataclass
class Request:
    url: str
    domain: str
    scantype: str


@dataclasses.dataclass
class Response:
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
    domains_csv = csv_request.content.decode("UTF-8").splitlines()
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
    domains: List[str], scantypes: List[str], date: Union[None, str] = None
) -> List[Request]:
    """
    construct_request builds requests for each endpoint using the scans
    and domains provided.
    """
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")

    requests = []
    for domain, scantype in product(domains, scantypes):
        endpoint = f"api/{API_VERSION}/date/{date}/domains/{domain}/{scantype}/"
        url = urljoin(API_URL, endpoint)
        request = Request(url, domain, scantype)
        requests.append(request)

    return requests


def random_list(num: int, list_: List[Any]) -> List[Any]:
    """
    random_list shuffles a list and returns the first n values, where n == num.
    """
    cryptogen = SystemRandom()
    cryptogen.shuffle(list_)
    return list_[:num]


def process_responses(responses: Tuple[Response]):
    error_count = 0
    errors = []
    total_requests = NUM_DOMAINS * len(SCAN_TYPES)

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
            print(f"Found {v} errors for the {k} scantype.")


async def main():
    print("Calculating baselines...")
    domains = await get_domains()
    random_domains = random_list(NUM_DOMAINS, domains)
    requests = construct_requests(random_domains, SCAN_TYPES, date="2020-08-26")
    responses = await test_api(requests)
    process_responses(responses)

    await client.aclose()
    return random_domains


if __name__ == "__main__":
    result = asyncio.run(main())
