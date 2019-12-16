from django.test import SimpleTestCase
from rest_framework.test import APIClient
import json

# tests for views


class CheckAPI(SimpleTestCase):
    client = APIClient()
    domainsresponse = client.get("/api/v1/domains/")
    domainsjsondata = json.loads(domainsresponse.content)
    scansresponse = client.get("/api/v1/scans/")
    scansjsondata = json.loads(scansresponse.content)

    def test_all_domains(self):
        """All domains are returned from calls to domains and scans endpoints"""
        self.assertGreaterEqual(len(self.domainsjsondata), 10)
        self.assertGreaterEqual(len(self.scansjsondata), 10)

    def test_domains_same_as_scans(self):
        """domains endpoint returns the same as the scans endpoint"""
        self.assertEqual(self.domainsjsondata, self.scansjsondata)

    def test_individual_domain_works(self):
        """domains/18f.gov endpoint works"""
        response = self.client.get("/api/v1/domains/18f.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 7)
        self.assertEqual(jsondata[0]['domain'], '18f.gov')

    def test_individual_scans_works(self):
        """scans/uswds2 endpoint works"""
        response = self.client.get("/api/v1/scans/uswds2/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 3)
        self.assertEqual(jsondata[0]['scantype'], 'uswds2')

    def test_dap_scan_works(self):
        """scans/dap endpoint works"""
        response = self.client.get("/api/v1/scans/dap/gsa.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'dap')
        self.assertIn('GSA', jsondata['data']['dap_parameters']['agency'])

    def test_thirdparty_scan_works(self):
        """scans/third_party endpoint works"""
        response = self.client.get("/api/v1/scans/third_parties/gsa.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'third_parties')
        self.assertIn('Digital Analytics Program', jsondata['data']['known_services'])

    def test_api_queries_domain(self):
        """queries with wildcards work"""
        response = self.client.get("/api/v1/domains/?domain=gsa*")
        jsondata = json.loads(response.content)
        # There are currently 7 scans, so this should get all the gsa scans
        self.assertEqual(len(jsondata), 7)

    def test_api_queries_dapdetect(self):
        """queries for nested fields work"""
        response = self.client.get("/api/v1/domains/?data.dap_detected=true")
        jsondata = json.loads(response.content)
        # this should get the gsa and 18f scans and not the afrh.gov scan
        self.assertEqual(len(jsondata), 2)

    def test_api_queries_domainfromscan(self):
        """queries from specific scan work"""
        response = self.client.get("/api/v1/scans/third_parties/?domain=gsa*")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 1)

    def test_api_queries_dapdetectfromdomain(self):
        """queries from specific domain work"""
        response = self.client.get("/api/v1/domains/18f.gov/?data.dap_detected=true")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 1)

    def test_api_queries_uswdsgreaterthan(self):
        """greaterthan queries work"""
        response = self.client.get("/api/v1/scans/uswds/?data.total_score=gt:50")
        jsondata = json.loads(response.content)
        # 18f and gsa should have scores greater than 50
        self.assertEqual(len(jsondata), 2)

    def test_api_queries_uswdslessthan(self):
        """lessthan queries work"""
        response = self.client.get("/api/v1/scans/uswds/?data.total_score=lt:50")
        jsondata = json.loads(response.content)
        # afrh.gov should have a score of 0
        self.assertEqual(len(jsondata), 1)

    def test_api_queries_multipleargs(self):
        """multiple query arguments should be ANDed together"""
        response = self.client.get("/api/v1/domains/?domain=18f*&data.status_code=200")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 3)
