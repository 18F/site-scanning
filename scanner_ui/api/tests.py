from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from .serializers import DomainsSerializer
from .views import getDomain
from django.conf import settings
import boto3
import os


# tests for views
class CheckBucketTest(APITestCase):
    """
    This test case checks that the bucketname is getting parsed properly
    """
    def test_bucket_parse(self):
        self.assertIsNotNone(settings.BUCKETNAME)

class GetAllDomainsTest(APITestCase):
    client = APIClient()

    def test_get_all_domains(self):
        """
        This test ensures that all domains
        exist when we make a GET request to the domains/ endpoint.
        XXX It only runs when VCAP_SERVICES is set (fix this someday)
        """
        if 'VCAP_SERVICES' in os.environ:
            # hit the API endpoint
            response = self.client.get(
                reverse("domains-list")
            )
            # fetch the data
            expected = getDomain()

            serialized = DomainsSerializer(expected, many=True)
            self.assertEqual(response.data, serialized.data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
