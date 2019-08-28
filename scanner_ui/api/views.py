from django.shortcuts import render
from django.conf import settings
import boto3
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import DomainsSerializer
import os
import json
import re
from collections import defaultdict

# Create your views here.

def getMetadatafromS3():
	s3_resource = boto3.resource('s3')
	return s3_resource.Bucket(os.environ['BUCKETNAME']).objects.all()

def getScanFromS3(path):
	s3_resource = boto3.resource('s3')
	response = s3_resource.Object(os.environ['BUCKETNAME'],path).get()
	return {'body': response['Body'].read(), 'lastmodified': response['LastModified']}


# This function provides a reference to the domain scan data in it's s3 bucket
# If scantype is None, then we want all the scans.
def getScantype(scantype=None):
	scans = []
	for f in getMetadatafromS3():
		if not re.search('\.json$', f.key):
			continue
		s3scantype = os.path.dirname(f.key)
		if scantype == None or s3scantype == scantype:
			scandomain = os.path.basename(os.path.splitext(f.key)[0])
			scan_data_url = "https://s3-" + os.environ['AWS_DEFAULT_REGION'] + ".amazonaws.com/" + os.environ['BUCKETNAME'] + "/" + f.key
			scans.append({"domain": scandomain, "scantype": s3scantype, "lastmodified": f.last_modified, "scan_data_url": scan_data_url})
	return scans

# get all the scans of the type and domain specified.  If the type is
# None, you get all of that scantype.  If the domain is None, you
# get all domains.
def getScans(scantype=None, domain=None):
	scans = []
	for f in getMetadatafromS3():
		if not re.search('\.json$', f.key):
			continue
		s3scantype = os.path.dirname(f.key)
		scandomain = os.path.basename(os.path.splitext(f.key)[0])
		if scantype == None or s3scantype == scantype:
			if domain == None or scandomain == domain:
				scandata = getScanFromS3(f.key)
				json_data = json.loads(scandata['body'])
				scans.append(json_data)
	return scans


# This function provides a reference to the scan data in it's s3 bucket
# If domain is None, then we want all the domains.
def getDomain(domain=None):
	scans = []
	for f in getMetadatafromS3():
		if not re.search('\.json$', f.key):
			continue
		scandomain = os.path.basename(os.path.splitext(f.key)[0])
		if domain == None or scandomain == domain:
			scantype = os.path.dirname(f.key)
			scan_data_url = "https://s3-" + os.environ['AWS_DEFAULT_REGION'] + ".amazonaws.com/" + os.environ['BUCKETNAME'] + "/" + f.key
			scans.append({"domain": scandomain, "scantype": scantype, "lastmodified": f.last_modified, "scan_data_url": scan_data_url})
	return scans


class DomainsViewset(viewsets.ViewSet):
	def list(self, request):
		domains = getDomain()
		serializer = DomainsSerializer(domains, many=True)
		return Response(serializer.data)

	def retrieve(self, request, domain=None):
		domains = getScans(domain=pk)
		serializer = DomainsSerializer(domains, many=True)
		return Response(serializer.data)

class ScansViewset(viewsets.ViewSet):
	def list(self, request):
		domains = getScantype()
		serializer = DomainsSerializer(domains, many=True)
		return Response(serializer.data)

	def retrieve(self, request, scantype=None):
		domains = getScantype(pk)
		serializer = DomainsSerializer(domains, many=True)
		return Response(serializer.data)

	def scan(self, request, scantype=None, domain=None):
		scan = getScans(scantype=scantype, domain=domain)
		if len(scan) != 1:
			raise Exception('too many or too few scans', scan)
		serializer = DomainsSerializer(scan[0])
		return Response(serializer.data)
