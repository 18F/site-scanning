#!/usr/bin/env python

"""
This module will print out a report on scan counts for each scan type.
Will returns results for today, or the specified date:

./utilities/get_scan_counts.py
./utilities/get_scan_counts.py 2020-05-20
"""

import pprint
import sys
from datetime import datetime

import requests


API_ROOT = "https://spotlight.app.cloud.gov/api/v1"
SCAN_TYPES = [
    "200scanner",
    "dap",
    "lighthouse",
    "pagedata",
    "privacy",
    "pshtt",
    "sitemap",
    "third_parties",
    "uswds2",
]


def _get_scan_counts(scan_date: str, scan_type: str):
    response = requests.get(f"{API_ROOT}/date/{scan_date}/scans/{scan_type}/")
    return response.json()["count"]


def _get_all_scan_counts(scan_date: str):
    return {
        scan_type: _get_scan_counts(scan_date, scan_type) for scan_type in SCAN_TYPES
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scan_dt = sys.argv[-1]
    else:
        scan_dt = datetime.now().strftime("%Y-%m-%d")
    pp = pprint.PrettyPrinter(indent=4)
    scan_counts = _get_all_scan_counts(scan_dt)
    pp.pprint(scan_counts)
