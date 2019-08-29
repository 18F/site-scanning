from django.shortcuts import render
from django.conf import settings
import boto3
from rest_framework import generics
from rest_framework import viewsets
from rest_framework import pagination
from rest_framework.response import Response
from .serializers import ScanSerializer
import os
import json
import re
from collections import defaultdict
from scanner_ui.ui.views import getdates
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

# Create your views here.


# get all the scans of the type and domain specified from ES.  If the type is
# None, you get all of that scantype.  If the domain is None, you
# get all domains.  If you supply a request, set the API url up
# for the scan using it.
def getScansFromES(scantype=None, domain=None, request=None):
	es = Elasticsearch([os.environ['ESURI']])
	dates = getdates()
	latestindex = dates[1] + '-*'
	indices = list(es.indices.get_alias(latestindex).keys())
	y, m, d, scantypes = zip(*(s.split("-") for s in indices))

	if scantype in scantypes:
		index = dates[1] + '-' + scantype
		s = Search(using=es, index=index)
	else:
		s = Search(using=es, index=latestindex)

	s = s.sort('domain')

	if domain != None:
		s = s.filter("term", domain=domain)

	if request != None:
		apiurl = request.scheme + '://' + request.get_host() + '/api/v1/scans/'

	scans = []
	for i in s.scan():
		if request != None:
			i['scan_data_url'] = apiurl + i['scantype'] + '/' + i['domain'] + '/'
		scans.append(i.to_dict())

	return scans

class ElasticsearchPagination(pagination.PageNumberPagination):
	def paginate_queryset(self, queryset, request, view=None):
		page_size = self.get_page_size(request)
		if not page_size:
			return None
		page_number = request.query_params.get(self.page_query_param, 1)
		if not page_number:
			return None
		start = page_size * (page_number - 1)
		finish = start + page_size
		return queryset[start:finish]


class DomainsViewset(viewsets.ViewSet):
	pagination_class = ElasticsearchPagination

	def list(self, request):
		scans = getScansFromES(request=request)
		serializer = ScanSerializer(scans, many=True)
		return Response(serializer.data)

	def retrieve(self, request, domain=None):
		scans = getScansFromES(domain=domain, request=request)
		serializer = ScanSerializer(scans, many=True)
		return Response(serializer.data)

class ScansViewset(viewsets.ViewSet):
	pagination_class = ElasticsearchPagination

	def list(self, request):
		scans = getScansFromES(request=request)
		serializer = ScanSerializer(scans, many=True)
		return Response(serializer.data)

	def retrieve(self, request, scantype=None):
		scans = getScansFromES(scantype=scantype, request=request)
		serializer = ScanSerializer(scans, many=True)
		return Response(serializer.data)

	def scan(self, request, scantype=None, domain=None):
		scan = getScansFromES(scantype=scantype, domain=domain, request=request)
		print('request is', request)
		if len(scan) != 1:
			raise Exception('too many or too few scans', scan)
		serializer = ScanSerializer(scan[0])
		return Response(serializer.data)
