from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from .serializers import ScansSerializer
from django.conf import settings
import boto3


# tests for views
class CheckBucketTest(APITestCase):
    """
    This test case checks that the bucketname is getting parsed properly
    """
    def test_bucket_parse(self):
        self.assertIsNotNone(settings.BUCKETNAME)

class GetAllScansTest(APITestCase):
    client = APIClient()

    def test_get_all_scans(self):
        """
        This test ensures that all scans
        exist when we make a GET request to the scans/ endpoint
        """
        # hit the API endpoint
        response = self.client.get(
            reverse("scans-all", kwargs={"version": "v1"})
        )
        # fetch the data
        boto3.setup_default_session(region_name=settings.AWS_REGION,aws_access_key_id=settings.AWS_KEY_ID,aws_secret_access_key=settings.AWS_ACCESS_KEY)
        s3_resource = boto3.resource('s3')
        expected = s3_resource.Bucket(settings.BUCKETNAME).objects.all()

        serialized = ScansSerializer(expected, many=True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

