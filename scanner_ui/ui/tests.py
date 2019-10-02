from django.test import SimpleTestCase
from django.test import Client
import csv
from .viewfunctions import getdates, getquery, getListFromFields, deperiodize, periodize, deslash, domainsWith, mixpagedatain

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
        self.assertEqual(s.count(), 2)

    def test_getlistfromfields(self):
        dates = getdates()
        index = dates[1] + '-200scanner'
        mylist = getListFromFields(index, 'domain')
        self.assertEqual(len(mylist), 2)

    def test_getlistfromfields_subfield(self):
        dates = getdates()
        index = dates[1] + '-pagedata'
        mylist = getListFromFields(index, 'data', subfield='content_type')
        self.assertTrue('application/json' in mylist)
        self.assertTrue('text/plain' in mylist)
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
        self.assertFalse('pagedata' in myscan)
        newscan = mixpagedatain(myscan, indexbase)
        self.assertTrue('pagedata' in newscan)
        self.assertTrue('/' in newscan['pagedata'])


class CheckUI(SimpleTestCase):
    client = Client()

    def test_home(self):
        """home page has proper data"""
        response = self.client.get("/")
        self.assertIn(b'Number of scans collected:</strong> 10', response.content)

    def test_about(self):
        """about page has proper data"""
        response = self.client.get("/about/")
        self.assertIn(b'You can contribute to the project', response.content)

    def test_json_pages(self):
        """json export pages should emit proper json"""
        pages = [
            '/search200/json/',
            '/searchUSWDS/json/',
            '/privacy/json/',
            '/sitemap/json/',
        ]
        for i in pages:
            response = self.client.get(i)
            self.assertGreaterEqual(len(response.json()), 2, msg=i)

    def test_csv_pages(self):
        """ csv pages should generate proper csv"""
        pages = [
            '/search200/csv/',
            '/searchUSWDS/csv/',
            '/privacy/csv/',
            '/sitemap/csv/',
        ]
        for i in pages:
            response = self.client.get(i)
            mycsv = csv.reader(str(response))
            csvlines = 0
            for z in mycsv:
                csvlines = csvlines + 1
            self.assertGreaterEqual(csvlines, 2, msg=i)

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
        self.assertNotIn(b'gsa.gov', response.content)
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
