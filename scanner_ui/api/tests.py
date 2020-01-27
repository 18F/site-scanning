from django.test import SimpleTestCase
from rest_framework.test import APIClient
import json
import datetime

# tests for views


class CheckAPI(SimpleTestCase):
    client = APIClient()
    domainsresponse = client.get("/api/v1/domains/")
    domainsjsondata = json.loads(domainsresponse.content)
    scansresponse = client.get("/api/v1/scans/")
    scansjsondata = json.loads(scansresponse.content)
    datesresponse = client.get("/api/v1/lists/dates/")
    datesjsondata = json.loads(datesresponse.content)

    def test_all_domains(self):
        """All domains are returned from calls to domains endpoint"""
        self.assertGreaterEqual(len(self.domainsjsondata), 10)

    def test_scans_list(self):
        """the scans endpoint gets you a list of scans"""
        self.assertGreaterEqual(len(self.scansjsondata), 7)
        self.assertIn('third_parties', self.scansjsondata)
        self.assertIn('dap', self.scansjsondata)
        self.assertIn('200scanner', self.scansjsondata)

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

    def test_domains_api_pagination(self):
        """pagination on domains endpoint should work"""
        response = self.client.get("/api/v1/domains/?page=1")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['count'], len(jsondata['results']))

    def test_scans_api_pagination(self):
        """pagination on scans endpoint should work"""
        response = self.client.get("/api/v1/scans/uswds2/?page=1")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['count'], len(jsondata['results']))

    def test_api_cors(self):
        """CORS should be enabled on the API"""
        response = self.client.get("/api/v1/domains/18f.gov/", HTTP_ORIGIN='localhost')
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')

    def test_dates_endpoint(self):
        """dates endpoint works"""
        response = self.client.get("/api/v1/lists/dates/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 1)
        d = datetime.datetime.now()
        self.assertEqual(jsondata[0], d.strftime("%Y-%m-%d"))

    def test_agencies_endpoint(self):
        """agencies endpoint works"""
        response = self.client.get("/api/v1/lists/dap/agencies/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertIn('General Services Administration', jsondata)

    def test_domaintypes_endpoint(self):
        """domaintypes endpoint works"""
        response = self.client.get("/api/v1/lists/dap/domaintypes/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 1)
        self.assertIn('Federal Agency - Executive', jsondata)

    def test_fieldvalues_domain_endpoint(self):
        """fieldvalues endpoint works"""
        response = self.client.get("/api/v1/lists/privacy/values/domain/")
        jsondata = json.loads(response.content)
        self.assertGreaterEqual(len(jsondata), 3)
        self.assertIn('18f.gov', jsondata)

    def test_fieldvalues_data_endpoint(self):
        """fieldvalues endpoint works"""
        response = self.client.get("/api/v1/lists/privacy/values/data/")
        jsondata = json.loads(response.content)
        self.assertGreaterEqual(len(jsondata), 3)

    def test_fieldvalues_nested_endpoint(self):
        """fieldvalues endpoint works with nested fields"""
        response = self.client.get("/api/v1/lists/dap/values/data.dap_detected/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertIn(True, jsondata)
        self.assertIn(False, jsondata)

    def test_fieldvalues_subfield(self):
        """fieldvalues endpoint works with subfields"""
        response = self.client.get("/api/v1/lists/pagedata/values/data/responsecode/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 3)
        self.assertIn('200', jsondata)
        self.assertIn('404', jsondata)
        self.assertIn('-1', jsondata)

    def test_all_domains_date(self):
        """All domains are returned from calls to domains endpoint with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/domains/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertGreaterEqual(len(jsondata), 10)

    def test_specific_domain_date(self):
        """All domains are returned from calls to domains endpoint with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/domains/18f.gov/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 7)
        self.assertEqual(jsondata[0]['domain'], '18f.gov')

    def test_specific_domain_scan_date(self):
        """requesting one particular scantype from one particular domain on a particular date works"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/domains/18f.gov/dap/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['domain'], '18f.gov')

    def test_scans_list_date(self):
        """the scans endpoint gets you a list of scans for a particular date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/scans/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertGreaterEqual(len(jsondata), 7)
        self.assertIn('third_parties', jsondata)
        self.assertIn('dap', jsondata)
        self.assertIn('200scanner', jsondata)

    def test_individual_scans_works_date(self):
        """the scans endpoint gets you a list of scans for a particular date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/scans/dap/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 3)
        self.assertEqual(jsondata[0]['scantype'], 'dap')

    def test_dap_scan_works_date(self):
        """the scans endpoint gets you a list of scans for a particular date and domain"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/scans/dap/gsa.gov/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'dap')
        self.assertIn('GSA', jsondata['data']['dap_parameters']['agency'])

    def test_agencies_endpoint_date(self):
        """agencies endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/dap/agencies/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertIn('General Services Administration', jsondata)

    def test_domaintypes_endpoint_date(self):
        """domaintypes endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/dap/domaintypes/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 1)
        self.assertIn('Federal Agency - Executive', jsondata)

    def test_fieldvalues_domain_endpoint_date(self):
        """fieldvalues endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/privacy/values/domain/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertGreaterEqual(len(jsondata), 3)
        self.assertIn('18f.gov', jsondata)

    def test_fieldvalues_data_endpoint_date(self):
        """fieldvalues endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/privacy/values/data/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertGreaterEqual(len(jsondata), 3)

    def test_fieldvalues_nested_endpoint_date(self):
        """fieldvalues endpoint works with nested fields with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/dap/values/data.dap_detected/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertIn(True, jsondata)
        self.assertIn(False, jsondata)

    def test_fieldvalues_subfield_date(self):
        """fieldvalues endpoint works with subfields with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/pagedata/values/data/responsecode/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 3)
        self.assertIn('200', jsondata)
        self.assertIn('404', jsondata)
        self.assertIn('-1', jsondata)
