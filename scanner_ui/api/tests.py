import csv
import datetime
import json
import io

from django.test import override_settings, SimpleTestCase
from rest_framework.test import APIClient


@override_settings(API_OMIT_TODAY=False)
class CheckAPI(SimpleTestCase):
    client = APIClient()
    domainsresponse = client.get("/api/v1/domains/")
    domainsjsondata = json.loads(domainsresponse.content)
    scansresponse = client.get("/api/v1/scans/")
    scansjsondata = json.loads(scansresponse.content)
    datesresponse = client.get("/api/v1/lists/dates/")
    datesjsondata = json.loads(datesresponse.content)
    numscans = 9
    numdomains = 7
    domains = [
        '18f.gov',
        'gsa.gov',
        'afrh.gov',
        'cloud.gov',
        'login.gov',
        'calendar.gsa.gov',
        '*.ecmapps.treasuryecm.gov'
    ]

    def test_all_domains(self):
        """All domains are returned from calls to domains endpoint"""
        domainlist = []
        for i in self.domainsjsondata['results']:
            domainlist.append(i['domain'])
        self.assertEqual(self.domainsjsondata['count'], self.numscans * self.numdomains)
        for i in self.domains:
            self.assertIn(i, domainlist)

    def test_scans_list(self):
        """the scans endpoint gets you a list of scans"""
        self.assertEqual(len(self.scansjsondata), self.numscans)
        self.assertIn('third_parties', self.scansjsondata)
        self.assertIn('dap', self.scansjsondata)
        self.assertIn('200scanner', self.scansjsondata)

    def test_individual_domain_works(self):
        """domains/18f.gov endpoint works"""
        response = self.client.get("/api/v1/domains/18f.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), self.numscans)
        self.assertEqual(jsondata[0]['domain'], '18f.gov')

    def test_org_field(self):
        """there is an organization field in the API"""
        response = self.client.get("/api/v1/domains/18f.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual('18F', jsondata[0]['organization'])

    def test_dap_scan_works(self):
        """scans/dap endpoint works"""
        response = self.client.get("/api/v1/scans/dap/gsa.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'dap')
        self.assertIn('GSA', jsondata['data']['dap_parameters'])

    def test_pshtt_scan_works(self):
        """scans/pshtt endpoint works"""
        response = self.client.get("/api/v1/scans/pshtt/gsa.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'pshtt')
        self.assertEqual(jsondata['data']['Base Domain'], 'gsa.gov')

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
        self.assertEqual(jsondata['count'], self.numscans)

    def test_api_queries_dapdetect(self):
        """queries for nested fields work"""
        response = self.client.get("/api/v1/domains/?data.dap_detected=true")
        # this should get the gsa and 18f scans and not the afrh.gov scan
        self.assertIn('"domain":"18f.gov"', str(response.content))
        self.assertIn('"domain":"gsa.gov"', str(response.content))
        self.assertNotIn('afrh.gov', str(response.content))

    def test_api_queries_domainfromscan(self):
        """queries from specific scan work"""
        response = self.client.get("/api/v1/scans/third_parties/?domain=gsa*")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['count'], 1)

    def test_api_queries_dapdetectfromdomain(self):
        """queries from specific domain work"""
        response = self.client.get("/api/v1/domains/18f.gov/?data.dap_detected=true")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 1)

    def test_api_queries_uswdsgreaterthan(self):
        """greaterthan queries work"""
        response = self.client.get("/api/v1/scans/uswds/?data.total_score=gt:50")
        jsondata = json.loads(response.content)
        # 18f and gsa and and login.gov and cloud.gov should have scores greater than 50
        self.assertEqual(len(jsondata), 4)

    def test_api_queries_uswdslessthan(self):
        """lessthan queries work"""
        response = self.client.get("/api/v1/scans/uswds/?data.total_score=lt:50")
        jsondata = json.loads(response.content)
        # afrh.gov should have a score of 0
        self.assertEqual(jsondata['count'], 3)

    def test_api_queries_multipleargs(self):
        """multiple query arguments should be ANDed together"""
        response = self.client.get("/api/v1/domains/?domain=18f*&data.status_code=200")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['count'], 3)

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

    def test_api_pagesize(self):
        """page_size on scans endpoint should work"""
        response = self.client.get("/api/v1/scans/uswds2/?page=1&page_size=2")
        jsondata = json.loads(response.content)
        self.assertEqual(2, len(jsondata['results']))

    def test_api_secondpage(self):
        """second page on scans endpoint should work and not be the same as the first page"""
        response2 = self.client.get("/api/v1/scans/uswds2/?page=2&page_size=2")
        jsondata2 = json.loads(response2.content)
        response = self.client.get("/api/v1/scans/uswds2/?page=1&page_size=2")
        jsondata = json.loads(response.content)
        self.assertEqual(2, len(jsondata2['results']))
        self.assertNotEqual(jsondata['results'], jsondata2['results'])

    def test_api_secondpagedomains(self):
        """second page on domains endpoint should work and not be the same as the first page"""
        response2 = self.client.get("/api/v1/domains/?page=2&page_size=1")
        jsondata2 = json.loads(response2.content)
        response = self.client.get("/api/v1/domains/?page=1&page_size=1")
        jsondata = json.loads(response.content)
        self.assertEqual(1, len(jsondata2['results']))
        self.assertNotEqual(jsondata['results'], jsondata2['results'])

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
        self.assertEqual(len(jsondata), 3)
        self.assertIn('General Services Administration', jsondata)

    def test_domaintypes_endpoint(self):
        """domaintypes endpoint works"""
        response = self.client.get("/api/v1/lists/dap/domaintypes/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertIn('Federal Agency - Executive', jsondata)

    def test_fieldvalues_domain_endpoint(self):
        """fieldvalues endpoint works"""
        response = self.client.get("/api/v1/lists/privacy/values/domain/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), self.numdomains)
        self.assertIn('18f.gov', jsondata)

    def test_fieldvalues_data_endpoint(self):
        """fieldvalues endpoint works"""
        response = self.client.get("/api/v1/lists/privacy/values/data/")
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 6)

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
        self.assertEqual(jsondata['count'], self.numscans * self.numdomains)

    def test_specific_domain_date(self):
        """All domains are returned from calls to domains endpoint with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/domains/18f.gov/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), self.numscans)
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
        self.assertEqual(len(jsondata), self.numscans)
        self.assertIn('third_parties', jsondata)
        self.assertIn('dap', jsondata)
        self.assertIn('200scanner', jsondata)

    def test_individual_scans_works_date(self):
        """the scans endpoint gets you a list of scans for a particular date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/scans/dap/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['count'], self.numdomains)
        self.assertEqual(jsondata['results'][0]['scantype'], 'dap')

    def test_dap_scan_works_date(self):
        """the scans endpoint gets you a list of scans for a particular date and domain"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/scans/dap/gsa.gov/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['scantype'], 'dap')
        self.assertIn('GSA', jsondata['data']['dap_parameters'])

    def test_agencies_endpoint_date(self):
        """agencies endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/dap/agencies/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 3)
        self.assertIn('General Services Administration', jsondata)

    def test_domaintypes_endpoint_date(self):
        """domaintypes endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/dap/domaintypes/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), 2)
        self.assertIn('Federal Agency - Executive', jsondata)

    def test_fieldvalues_domain_endpoint_date(self):
        """fieldvalues endpoint works with a date"""
        url = '/api/v1/date/' + self.datesjsondata[0] + '/lists/privacy/values/domain/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(len(jsondata), self.numdomains)
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

    def test_fieldvalues_uswdsversion(self):
        """fieldvalues endpoint works for uswdsversion field"""
        url = '/api/v1/lists/uswds2/values/data.uswdsversion/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertIn('v2.6.0', jsondata)

    def test_subdomains_work(self):
        """test calendar.gsa.gov subdomain exists"""
        url = '/api/v1/domains/calendar.gsa.gov/'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata[0]['domain'], 'calendar.gsa.gov')

    def test_pagetoofar_work(self):
        """test that a page that is too big returns an empty page"""
        url = '/api/v1/domains/?page=9999999999999999'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata, [])

    def test_negativepage_work(self):
        """test that a page that is negative returns an empty page"""
        url = '/api/v1/domains/?page=-12'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata, [])

    def test_invalidpage_work(self):
        """test that a page that is not an integer returns an empty page"""
        url = '/api/v1/domains/?page=foo'
        response = self.client.get(url)
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata, [])

    def test_scans_csv(self):
        """test that the CSV endpoint returns the proper list of domains"""
        url = '/api/v1/scans/dap/csv/'
        response = self.client.get(url)
        domainlist = set()
        count = 0

        # Parse CSV by hand here.  csv.DictReader can't handle encoded inputs.
        for row in response.streaming_content:
            rowlist = row.decode('utf-8').split(',')
            domain = rowlist[0]
            if domain != 'domain' and count != 0:
                self.assertIn(domain, self.domains)
            domainlist = domainlist | {domain}
            count = count + 1
        for i in self.domains:
            self.assertIn(i, domainlist)

    def test_scans_csvwithquery(self):
        """test that the CSV endpoint returns the proper domain when we add query parameters"""
        url = '/api/v1/scans/dap/csv/?domain=gsa.gov'
        response = self.client.get(url)
        count = 0

        for row in response.streaming_content:
            rowlist = row.decode('utf-8').split(',')
            domain = rowlist[0]
            if domain != 'domain' and count != 0:
                self.assertEqual(domain, 'gsa.gov')
            count = count + 1

    def test_cv_scan(self):
        """scan for coronavirus page works"""
        response = self.client.get("/api/v1/scans/200scanner/gsa.gov/")
        jsondata = json.loads(response.content)
        self.assertEqual(jsondata['data']['/coronavirus'], '200')
