from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from .serializers import ScanSerializer
from .views import getScansFromES
from django.conf import settings
import boto3
import os


# tests for views

class GetAllScansTest(APITestCase):
    client = APIClient()

    def test_get_all_scans(self):
        """
        This test ensures that all domains
        exist when we make a GET request to the domains/ endpoint.
        """
        # hit the API endpoint
        response = self.client.get(
            reverse("scans-list")
        )
        # fetch the data
        expected = getScans()

        serialized = ScanSerializer(expected, many=True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
