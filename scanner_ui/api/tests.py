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
        self.assertEqual(len(jsondata), 6)
        self.assertEqual(jsondata[0]['domain'], '18f.gov')

    def test_individual_scans_works(self):
        """scans/uswds2 endpoint works"""
        response = self.client.get("/api/v1/scans/uswds2/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertEqual(jsondata[0]['scantype'], 'uswds2')

    def test_dap_scans_works(self):
        """scans/dap endpoint works"""
        response = self.client.get("/api/v1/scans/dap/gsa.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'dap')
        self.assertEqual(jsondata['data']['dap_parameters']['agency'], 'GSA')
