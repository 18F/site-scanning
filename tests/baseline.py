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
from itertools import islice, product
from random import SystemRandom
from typing import Any, List, Union, Tuple
from urllib.parse import urljoin

import httpx

API_URL = "https://site-scanning.app.cloud.gov/"
API_VERSION = "v1"
NUM_TESTS = 100
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


async def main():
    domains = await get_domains()
    random_domains = random_list(NUM_TESTS, domains)
    requests = construct_requests(random_domains, SCAN_TYPES, date="2020-08-26")
    results = await test_api(requests)

    for result in results:
        print(f"Request to {result.request.url} returned a {result.status}")

    await client.aclose()
    return random_domains


if __name__ == "__main__":
    result = asyncio.run(main())
