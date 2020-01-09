from django.test import SimpleTestCase
from django.test import Client
import csv
import re
from .viewfunctions import getdates, getquery, getListFromFields, deperiodize, periodize, deslash, domainsWith, mixpagedatain, popupbuilder

# Create your tests here.


class checkviewfunctions(SimpleTestCase):
    def test_getdates(self):
        dates = getdates()
        self.assertEqual(len(dates), 2)
        self.assertRegex(dates[1], r'^[0-9]{4}-[0-9]{2}-[0-9]{2}')

    def test_checkgetquery(self):
        dates = getdates()
        index = dates[1] + '-200scanner'
        s = getquery(index)
        self.assertEqual(s.count(), 3)

    def test_getquerydomainsearch(self):
        dates = getdates()
        index = dates[1] + '-200scanner'
        s = getquery(index, domainsearch='18f')
        self.assertEqual(s.count(), 1)

    def test_getquerydapsearch(self):
        dates = getdates()
        index = dates[1] + '-dap'
        s = getquery(index, present='DAP Present', displaytype='dap')
        self.assertEqual(s.count(), 2)

    def test_getlistfromfields(self):
        dates = getdates()
        index = dates[1] + '-200scanner'
        mylist = getListFromFields(index, 'domain')
        self.assertEqual(len(mylist), 3)

    def test_getlistfromfields_subfield(self):
        dates = getdates()
        index = dates[1] + '-pagedata'
        mylist = getListFromFields(index, 'data', subfield='content_type')
        self.assertTrue('application/json' in mylist)
        self.assertTrue('application/xml' in mylist)
        self.assertGreaterEqual(len(mylist), 4)

    def test_deperiodize(self):
        mystring = '/data.json'
        self.assertEqual(deperiodize(mystring), '/data//json')

    def test_periodize(self):
        mystring = '/data//json'
        self.assertEqual(periodize(mystring), '/data.json')

    def test_deslash(self):
        mystring = '/data.json'
        self.assertEqual(deslash(mystring), '\/data.json')

    def test_domainswith(self):
        dates = getdates()
        index = dates[1] + '-pagedata'
        domains = domainsWith('/privacy', 'responsecode', '200', index)
        self.assertEqual(len(domains), 1)

    def test_mixpagedatain(self):
        dates = getdates()
        indexbase = dates[1]
        index = indexbase + '-200scanner'
        s = getquery(index)
        r = s.execute()
        myscan = r.hits[0].to_dict()
        self.assertFalse('extradata' in myscan)
        newscan = mixpagedatain(myscan, indexbase)
        self.assertTrue('extradata' in newscan)
        self.assertTrue('/' in newscan['extradata'])

        newscan = mixpagedatain(myscan, indexbase, 'dap')
        self.assertTrue('extradata' in newscan)
        self.assertTrue('dap_detected' in newscan['extradata'])

    def test_popupbuilder(self):
        presentlist = ['Present', "Not Present", "All"]
        present = "All"
        p = popupbuilder('present', presentlist, selectedvalue=present)
        popup = {'name': 'present', 'disabled': '', 'values': {'Present': '', 'Not Present': '', 'All': 'selected'}}
        self.assertEqual(popup, p)

        p = popupbuilder('present', presentlist, selectedvalue=present, disabled=True)
        popup = {'name': 'present', 'disabled': 'disabled', 'values': {'Present': '', 'Not Present': '', 'All': 'selected'}}
        self.assertEqual(popup, p)


class CheckUI(SimpleTestCase):
    client = Client()

    def test_home(self):
        """home page has proper data"""
        response = self.client.get("/")
        self.assertIn(b'Number of scans collected:</strong>', response.content)
        res = re.findall(r'Number of scans collected:</strong> (.*)</li>', response.content.decode())
        self.assertGreaterEqual(int(res[0]), 12)

    def test_about(self):
        """about page has proper data"""
        response = self.client.get("/about/")
        self.assertIn(b'You can contribute to the project', response.content)

    def test_scans(self):
        """scans page has proper data"""
        response = self.client.get("/scans/")
        self.assertIn(b'This page describes each of the active scans and provides more information about them', response.content)

    def test_downloads(self):
        """downloads page has proper data"""
        response = self.client.get("/downloads/")
        self.assertIn(b'This page lists each of the download links or API endpoints for data that is generated by the scans', response.content)

    def test_json_pages(self):
        """json export pages should emit proper json"""
        pages = [
            '/search200/json/',
            '/searchUSWDS/json/',
            '/searchUSWDS/json/?date=Scan%20Date&version=all%20versions&q=10&agency=All%20Agencies&domaintype=All%20Branches',
            '/search200/json/?200page=/code.json&date=Scan%20Date&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=application/json',
            '/privacy/json/',
            '/sitemap/json/',
            '/search200/json/?200page=All%20Scans&date=None&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=third_parties&domainsearch=None',
        ]
        for i in pages:
            response = self.client.get(i)
            self.assertGreaterEqual(len(response.json()), 1, msg=i)

        response = self.client.get('/search200/json/?200page=All%20Scans&date=None&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=dap')
        self.assertIn(b'dap_detected', response.content)

    def test_domain_filtered_json_page(self):
        """json export pages filtered by domain should emit proper json"""
        response = self.client.get('/search200/json/?200page=All%20Scans&date=Scan%20Date&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=third_parties&domainsearch=gsa')
        self.assertIn(b'gsa', response.content)
        self.assertNotIn(b'18f', response.content)

    def test_mimetypes(self):
        """if we select a mimetype, we should not get other mimetypes"""
        page = '/search200/200-codejson/?present=All&200page=%2Fcode.json&mimetype=application%2Fxml'
        response = self.client.get(page)
        self.assertNotIn(b'<td>text/html', response.content)
        self.assertNotIn(b'<td>application/json', response.content)

    def test_selected_mimetypes(self):
        """if we select a mimetype, we should get that mimetype"""
        page = '/search200/200-codejson/?present=All&200page=%2Fcode.json&mimetype=application%2Fjson'
        response = self.client.get(page)
        self.assertNotIn(b'<td>text/html', response.content)
        self.assertIn(b'<td>application/json', response.content)

    def test_csv_pages(self):
        """ csv pages should generate proper csv"""
        pages = [
            '/search200/csv/',
            '/search200/csv/?200page=/code.json&date=Scan%20Date&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present',
            '/searchUSWDS/csv/',
            '/privacy/csv/',
            '/sitemap/csv/',
            '/search200/csv/?200page=All%20Scans&date=None&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=dap&domainsearch=None',
        ]
        for i in pages:
            response = self.client.get(i)
            mycsv = csv.reader(str(response))
            csvlines = len(list(mycsv))
            self.assertGreaterEqual(csvlines, 2, msg=i)

    def test_dapcsv_pages(self):
        """ DAP csv page should work"""
        response = self.client.get('/search200/csv/?200page=All%20Scans&date=None&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=dap')
        self.assertIn(b'gsa', response.content)

    def test_thirdpartycsv_pages(self):
        """ third_party csv page should return correct data """
        response = self.client.get('/search200/csv/?200page=All%20Scans&date=None&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=third_parties&domainsearch=None')
        self.assertIn(b'unknown_services', response.content)
        self.assertIn(b'Digital Analytics Program', response.content)

    def test_domain_filtered_csv_pages(self):
        """ csv pages filtered by domain should generate proper csv"""
        response = self.client.get('/search200/csv/?200page=All%20Scans&date=Scan%20Date&agency=All%20Agencies&domaintype=All%20Branches&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=third_parties&domainsearch=gsa')
        self.assertIn(b'gsa', response.content)
        self.assertNotIn(b'18f', response.content)

    def test_agency_filtered_csv_pages(self):
        """ csv pages filtered by agency should generate proper csv"""
        response = self.client.get('/search200/csv/?200page=All%20Scans&date=Scan%20Date&agency=All%20Agencies&domaintype=Federal%20Agency%20-%20Executive&org=All%20Organizations&mimetype=all%20content_types&present=Present&displaytype=third_parties&domainsearch=')
        self.assertIn(b'gsa', response.content)

    def test_200page_nopageselected(self):
        """200scanner page responds properly without a page selected"""
        response = self.client.get('/search200/')
        self.assertIn(b'200 Scans Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertNotIn(b'<td>200</td>', response.content)

    def test_200page_pageselected(self):
        """200scanner page responds properly with a page selected (defaults to present)"""
        response = self.client.get('/search200/', {'200page': '/privacy'})
        self.assertIn(b'200 Scans Search', response.content)
        self.assertNotIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)
        self.assertNotIn(b'<td>404</td>', response.content)

    def test_200page_present(self):
        """200scanner page responds properly when we select present"""
        response = self.client.get('/search200/', {'present': 'Present', '200page': '/privacy'})
        self.assertIn(b'200 Scans Search', response.content)
        self.assertNotIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)
        self.assertNotIn(b'<td>404</td>', response.content)

    def test_200page_notpresent(self):
        """200scanner page responds properly when we select not present"""
        response = self.client.get('/search200/', {'present': 'Not Present', '200page': '/privacy'})
        self.assertIn(b'200 Scans Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertNotIn(b'https://gsa.gov', response.content)
        self.assertIn(b'<td>404</td>', response.content)
        self.assertNotIn(b'<td>200</td>', response.content)

    def test_200page_allpresent(self):
        """200scanner page responds properly when we select all present"""
        response = self.client.get('/search200/', {'present': 'All', '200page': '/privacy'})
        self.assertIn(b'200 Scans Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)
        self.assertIn(b'<td>404</td>', response.content)

    def test_present(self):
        response = self.client.get('/privacy/', {'present': 'Present'})
        self.assertIn(b'/privacy Page', response.content)
        self.assertIn(b'gsa.gov', response.content)

    def test_not_present(self):
        response = self.client.get('/privacy/', {'present': 'Not Present'})
        self.assertIn(b'/privacy Page', response.content)
        self.assertIn(b'18f.gov', response.content)

    def test_all_present(self):
        response = self.client.get('/privacy/', {'present': 'All'})
        self.assertIn(b'/privacy Page', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'18f.gov', response.content)

    def test_200devpage(self):
        """search200/200-developer page responds properly"""
        response = self.client.get('/search200/200-developer/', {'200page': '/data.json', 'mimetype': 'application/json'})
        self.assertIn(b'api.data.gov Search', response.content)
        self.assertNotIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)

    def test_200datapage(self):
        """search200/200-200-data.json page responds properly"""
        response = self.client.get('/search200/200-data.json/', {'200page': '/data.json', 'mimetype': 'application/json'})
        self.assertIn(b'data.gov Scan Search', response.content)
        self.assertNotIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)

    def test_200dappage(self):
        """search200/dap/ page responds properly"""
        response = self.client.get('/search200/dap/')
        self.assertIn(b'DAP Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'afrh.gov', response.content)
        self.assertIn(b'True', response.content)
        self.assertIn(b'False', response.content)

        response = self.client.get('/search200/dap/?present=All')
        self.assertIn(b'DAP Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'afrh.gov', response.content)
        self.assertIn(b'True', response.content)
        self.assertIn(b'False', response.content)

        response = self.client.get('/search200/dap/?present=DAP%20Present')
        self.assertIn(b'DAP Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'True', response.content)
        self.assertNotIn(b'False', response.content)

        response = self.client.get('/search200/dap/?present=DAP%20Not%20Present')
        self.assertIn(b'DAP Scan Search', response.content)
        self.assertIn(b'afrh.gov', response.content)
        self.assertIn(b'False', response.content)
        self.assertNotIn(b'True', response.content)

    def test_200thirdpartyservicespage(self):
        """search200/third_parties/ page responds properly"""
        response = self.client.get('/search200/third_parties/')
        self.assertIn(b'Third Party Services Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'Known Services', response.content)
        self.assertIn(b'Digital Analytics Program', response.content)

    def test_200codejsonpage(self):
        """search200/200-codejson page responds properly"""
        response = self.client.get('/search200/200-codejson/', {'200page': '/code.json', 'mimetype': 'application/json'})
        self.assertIn(b'code.gov Scan Search', response.content)
        self.assertNotIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)

    def test_200robotstxtpage(self):
        """search200/200-robotstxt page responds properly"""
        response = self.client.get('/search200/200-robotstxt/', {'200page': '/robots.txt'})
        self.assertIn(b'robots.txt Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)

    def test_uswdspages(self):
        """USWDS pages all respond properly"""
        response = self.client.get('/searchUSWDS/')
        self.assertIn(b'USWDS Scans Search', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'18f.gov', response.content)

    def test_privacypages(self):
        """privacy pages all respond properly"""
        response = self.client.get('/privacy/')
        self.assertIn(b'/privacy Page', response.content)
        self.assertNotIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)

    def test_sitemappages(self):
        """sitemap pages all respond properly"""
        response = self.client.get('/sitemap/')
        self.assertIn(b'Sitemap Page', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
        self.assertIn(b'<td>200</td>', response.content)

    def test_ui_cors(self):
        """CORS should not be enabled on the UI"""
        response = self.client.get("/about/")
        self.assertNotIn('Access-Control-Allow-Origin', response)
