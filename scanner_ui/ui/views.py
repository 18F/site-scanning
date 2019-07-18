from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import os
import datetime
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

# Create your views here.

es = Elasticsearch([os.environ['ESURI']])

def index(request):
	indexlist = es.indices.get_alias().keys()
	datemap = {}
	for i in indexlist:
		a = i.split('-', maxsplit=3)
		date = '-'.join(a[0:3])
		datemap[date] = 1
	dates = list(datemap.keys())
	dates.sort(reverse=True)
	latestindex = dates[0] + '-*'

	allscanscount = Search(using=es, index=latestindex).query().count()

	scantypecount = len(es.indices.get_alias(latestindex))

	s = Search(using=es, index=latestindex).query().source(['domain'])
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
	# search in ES for dates we can search in
	indexlist = es.indices.get_alias().keys()
	datemap = {}
	for i in indexlist:
		a = i.split('-', maxsplit=3)
		date = '-'.join(a[0:3])
		datemap[date] = 1
	dates = list(datemap.keys())
	dates.sort(reverse=True)
	dates.insert(0, 'latest')

	date = request.GET.get('date')
	if date == None or date == 'latest':
		index = dates[1]
	else:
		index = date

	# get scantype and if selected, use that index, otherwise search all indexes.
	scantype = request.GET.get('scantype')
	if scantype == None or scantype == ' all':
		index = index + '-*'
	else:
		index = index + '-' + scantype

	# search for scantypes in ES
	s = Search(using=es, index=dates[1] + '-*').query().source(['scantype'])
	scantypemap = {}
	for i in s.scan():
	        scantypemap[i.scantype] = 1
	scantypes = list(scantypemap.keys())
	scantypes.insert(0, ' all')

	# do the actual query here.  Start out with an empty query if this is our first time.
	query = request.GET.get('q')
	if query == None:
		# XXX this is ugly, but I don't know how to get an empty search yet
		s = Search(using=es, index=index).query("match", nothingrealblahblah=-22339)
	else:
		s = Search(using=es, index=index).query("simple_query_string", query=query)

	# set up pagination here
	page_no = request.GET.get('page')
	paginator = Paginator(s, 50)
	try:
		page = paginator.page(page_no)
	except PageNotAnInteger:
		page = paginator.page(1)
	except EmptyPage:
		page = paginator.page(paginator.num_pages)
	results = page.object_list.execute()
	# XXX make the results be a list that looks pretty

	context = {
		'search_results': results.hits,
		'scantypes': scantypes,
		'dates': dates,
		'query': query,
		'selected_scantype': scantype,
		'selected_date': date,
		'page_obj': page,
	}

	return render(request, "search.html", context=context)

def search200(request):
	# search in ES for dates we can search in
	indexlist = es.indices.get_alias().keys()
	datemap = {}
	for i in indexlist:
		a = i.split('-', maxsplit=3)
		date = '-'.join(a[0:3])
		datemap[date] = 1
	dates = list(datemap.keys())
	dates.sort(reverse=True)
	dates.insert(0, 'latest')

	date = request.GET.get('date')
	if date == None or date == 'latest':
		index = dates[1]
	else:
		index = date

	scantype = '200scanner'
	index = index + '-' + scantype

	# search in ES for 200 pages we can select
	my200page = request.GET.get('200page')
	if my200page == None:
		my200page == ' all'
	s = Search(using=es, index=index).query().params(terminate_after=1)
	pagemap = {}
	for i in s.scan():
			for z in i.data.to_dict().keys():
				pagemap[z] = 1
	my200pages = list(pagemap.keys())
	my200pages.insert(0, ' all')

	# do the actual query here.  Start out with an empty query if this is our first time.
	query = request.GET.get('q')
	if query == None:
		# XXX this is ugly, but I don't know how to get an empty search yet
		s = Search(using=es, index=index).query("match", nothingrealblahblah=-22339)
	else:
		if my200page == ' all':
			s = Search(using=es, index=index).query("simple_query_string", query=query)
		else:
			s = Search(using=es, index=index).query("simple_query_string", query=query, fields=[my200page])

	# set up pagination here
	page_no = request.GET.get('page')
	paginator = Paginator(s, 50)
	try:
		page = paginator.page(page_no)
	except PageNotAnInteger:
		page = paginator.page(1)
	except EmptyPage:
		page = paginator.page(paginator.num_pages)
	results = page.object_list.execute()
	# XXX make the results be a list that looks pretty

	context = {
		'search_results': results.hits,
		'dates': dates,
		'query': query,
		'selected_date': date,
		'selected_200page': my200page,
		'my200pages': my200pages,
		'page_obj': page,
	}

	return render(request, "search200.html", context=context)
