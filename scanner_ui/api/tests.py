import json

from django.test import SimpleTestCase
from rest_framework.test import APIClient


class CheckAPI(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_meta(self):
        """
        Test that the meta endpoint returns the version.
        """
        response = self.client.get("/api/v1/meta/")
        result = json.loads(response.content)
        expected = {"version": "v1"}
        self.assertEqual(expected, result)
