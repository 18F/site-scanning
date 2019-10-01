from django.test import SimpleTestCase
from django.test import Client
import csv

# Create your tests here.


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

    def test_200page(self):
        """200scanner page responds properly"""
        response = self.client.get('/search200/')
        self.assertIn(b'200 Scans Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)

    def test_200devpage(self):
        """search200/200-developer page responds properly"""
        response = self.client.get('/search200/200-developer/')
        self.assertIn(b'api.data.gov Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)

    def test_200codejsonpage(self):
        """search200/200-developer page responds properly"""
        response = self.client.get('/search200/200-codejson/')
        self.assertIn(b'code.gov Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)

    def test_200robotstxtpage(self):
        """search200/200-developer page responds properly"""
        response = self.client.get('/search200/200-robotstxt/')
        self.assertIn(b'robots.txt Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)

    def test_200datapage(self):
        """search200/200-developer page responds properly"""
        response = self.client.get('/search200/200-data.json/')
        self.assertIn(b'data.gov Scan Search', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)

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

    def test_sitemappages(self):
        """sitemap pages all respond properly"""
        response = self.client.get('/sitemap/')
        self.assertIn(b'Sitemap Page', response.content)
        self.assertIn(b'18f.gov', response.content)
        self.assertIn(b'gsa.gov', response.content)
