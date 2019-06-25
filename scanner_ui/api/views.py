from django.shortcuts import render
import boto3
from rest_framework import generics
from .serializers import DomainsSerializer
from django.conf import settings
import os
from collections import defaultdict

# Create your views here.
def getScansfromS3():
	boto3.setup_default_session(region_name=settings.AWS_REGION,aws_access_key_id=settings.AWS_KEY_ID,aws_secret_access_key=settings.AWS_ACCESS_KEY)
	s3_resource = boto3.resource('s3')

	scans = defaultdict(list)
	for o in s3_resource.Bucket(settings.BUCKETNAME).objects.all():
		domain = os.path.basename(o.key)
		scantype = os.path.dirname(o.key)
		scans[domain].append(scantype)

	queryset = []
	for domain in scans:
		queryset.append({"domain": domain, "scans": scans[domain]})
	return queryset

class ListDomainsView(generics.ListAPIView):
	"""
	Provides a get method handler.
	"""
	queryset = getScansfromS3()

	serializer_class = DomainsSerializer
