from django.shortcuts import render
import boto3
from rest_framework import generics
from .serializers import DomainsSerializer
from .serializers import ScansSerializer
from django.conf import settings
import os
from collections import defaultdict

# Create your views here.

def getScansFromS3():
	scans = defaultdict(list)
	for f in getMetadatafromS3():
		domain = os.path.basename(f.key)
		scantype = os.path.dirname(f.key)
		scans[scantype].append(domain)

	queryset = []
	for scantype in scans:
		queryset.append({"scan": scantype, "domains": scans[scantype]})
	return queryset

def getDomainsFromS3():
	scans = defaultdict(list)
	for f in getMetadatafromS3():
		domain = os.path.basename(f.key)
		scantype = os.path.dirname(f.key)
		scans[domain].append(scantype)

	queryset = []
	for domain in scans:
		queryset.append({"domain": domain, "scans": scans[domain]})
	return queryset

def getMetadatafromS3():
	boto3.setup_default_session(region_name=settings.AWS_REGION,aws_access_key_id=settings.AWS_KEY_ID,aws_secret_access_key=settings.AWS_ACCESS_KEY)
	s3_resource = boto3.resource('s3')
	return s3_resource.Bucket(settings.BUCKETNAME).objects.all()

class ListDomainsView(generics.ListAPIView):
	"""
	Provides a get method handler.
	"""
	queryset = getDomainsFromS3()

	serializer_class = DomainsSerializer

class ListScansView(generics.ListAPIView):
	"""
	Provides a get method handler.
	"""
	queryset = getScansFromS3()

	serializer_class = ScansSerializer
