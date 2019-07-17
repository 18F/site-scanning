from django.shortcuts import render
import os
import datetime
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

# Create your views here.

es = Elasticsearch([os.environ['ESURI']])

def index(request):
	yesterdayindex = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d-") + '*'

	allscanscount = Search(using=es, index=yesterdayindex).query().count()

	scantypecount = len(es.indices.get_alias(yesterdayindex))

	s = Search(using=es, index=yesterdayindex).query().source(['domain'])
	domainmap = {}
	for i in s.scan():
	        domainmap[i.domain] = 1
	domaincount = len(domainmap)

	context = {
		'num_domains': domaincount,
		'num_scantypes': scantypecount,
		'num_scans': allscanscount,
	}
	return render(request, "index.html", context=context)

def search(request):
	# search in ES for dates
	indexlist = es.indices.get_alias().keys()
	datemap = {}
	for i in indexlist:
		a = i.split('-', maxsplit=3)
		date = '-'.join(a[0:3])
		datemap[date] = 1
	dates = list(datemap.keys())
	dates.sort(reverse=True)

	date = request.GET.get('date')
	if date == None:
		index = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
		date = dates[0]
	else:
		index = date

	scantype = request.GET.get('scantype')
	if scantype == None or scantype == ' all':
		index = index + '-*'
	else:
		index = index + '-' + scantype

	# search for scantypes in ES
	s = Search(using=es, index=index).query().source(['scantype'])
	scantypemap = {}
	for i in s.scan():
	        scantypemap[i.scantype] = 1
	scantypes = list(scantypemap.keys())
	scantypes.insert(0, ' all')

	# do the actual query here.  Start out with an empty query if this is our first time.
	query = request.GET.get('q')
	if query == None:
		s = []
	else:
		s = Search(using=es, index=index).query()

	context = {
		'search_results': s,
		'scantypes': scantypes,
		'dates': dates,
		'query': query,
		'selected_scantype': scantype,
		'selected_date': date,
	}

	return render(request, "search.html", context=context)
