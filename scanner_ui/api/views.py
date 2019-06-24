from django.shortcuts import render
import boto3
from rest_framework import generics
from .serializers import ScansSerializer
from django.conf import settings

# Create your views here.

class ListScansView(generics.ListAPIView):
    """
    Provides a get method handler.
    """
    boto3.setup_default_session(region_name=settings.AWS_REGION,aws_access_key_id=settings.AWS_KEY_ID,aws_secret_access_key=settings.AWS_ACCESS_KEY)
    s3_resource = boto3.resource('s3')
    queryset = s3_resource.Bucket(settings.BUCKETNAME).objects.all()
    serializer_class = ScansSerializer
