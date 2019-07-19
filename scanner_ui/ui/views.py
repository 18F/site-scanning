from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import os
import datetime
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range, Bool

# Create your views here.

es = Elasticsearch([os.environ['ESURI']])

def getdates():
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
	return dates

def index(request):
	dates = getdates()
	latestindex = dates[1] + '-*'

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
	dates = getdates()

	date = request.GET.get('date')
	if date == None or date == 'latest':
		index = dates[1]
	else:
		index = date

	# get scantype and if selected, use that index, otherwise search all indexes.
	scantype = request.GET.get('scantype')
	if scantype == None or scantype == ' all scantypes':
		index = index + '-*'
	else:
		index = index + '-' + scantype

	# search for scantypes in ES
	s = Search(using=es, index=dates[1] + '-*').query().source(['scantype'])
	scantypemap = {}
	for i in s.scan():
	        scantypemap[i.scantype] = 1
	scantypes = list(scantypemap.keys())
	scantypes.insert(0, ' all scantypes')

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
	dates = getdates()

	date = request.GET.get('date')
	if date == None or date == 'latest':
		index = dates[1]
	else:
		index = date
	index = index + '-200scanner'

	# search in ES for 200 pages we can select
	my200page = request.GET.get('200page')
	if my200page == None:
		my200page == ' all pages'
	s = Search(using=es, index=index).query().params(terminate_after=1)
	pagemap = {}
	for i in s.scan():
			for z in i.data.to_dict().keys():
				pagemap[z] = 1
	my200pages = list(pagemap.keys())
	my200pages.insert(0, ' all pages')

	# search in ES for the agencies/domaintype
	s = Search(using=es, index=index).query().source(['agency', 'domaintype'])
	agencymap = {}
	domaintypemap = {}
	for i in s.scan():
	        agencymap[i.agency] = 1
	        domaintypemap[i.domaintype] = 1
	agencies = list(agencymap.keys())
	agencies.sort()
	agencies.insert(0, 'all agencies')
	domaintypes = list(domaintypemap.keys())
	domaintypes.sort()
	domaintypes.insert(0, 'all Types/Branches')

	agency = request.GET.get('agency')
	if agency == None:
		agency = 'all agencies'

	domaintype = request.GET.get('domaintype')
	if domaintype == None:
		domaintype = 'all Types/Branches'

	# do the actual query here.  Start out with an empty query if this is our first time.
	query = request.GET.get('q')
	s = Search(using=es, index=index)
	if query == None:
		# XXX this is ugly, but I don't know how to get an empty search yet
		s = s.query("match", nothingrealblahblah=-22339)
	else:
		if my200page == ' all pages':
			s = s.query("simple_query_string", query=query)
		else:
			field = 'data.' + my200page
			s = s.query("simple_query_string", query=query, fields=[field])
		if agency != 'all agencies':
			agencyquery = '"' + agency + '"'
			s = s.query("query_string", query=agencyquery, fields=['agency'])
		if domaintype != 'all Types/Branches':
			domaintypequery = '"' + domaintype + '"'
			s = s.query("query_string", query=domaintypequery, fields=['domaintype'])

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

	context = {
		'search_results': results.hits,
		'dates': dates,
		'query': query,
		'selected_date': date,
		'selected_200page': my200page,
		'my200pages': my200pages,
		'page_obj': page,
		'agencies': agencies,
		'selected_agency': agency,
		'domaintypes': domaintypes,
		'selected_domaintype': domaintype,
	}

	return render(request, "search200.html", context=context)

def searchUSWDS(request):
	dates = getdates()

	date = request.GET.get('date')
	if date == None or date == 'latest':
		index = dates[1]
		date = 'latest'
	else:
		index = date
	index = index + '-uswds2'

	# search in ES for the agencies/domaintype
	s = Search(using=es, index=index).query().source(['agency', 'domaintype'])
	agencymap = {}
	domaintypemap = {}
	for i in s.scan():
	        agencymap[i.agency] = 1
	        domaintypemap[i.domaintype] = 1
	agencies = list(agencymap.keys())
	agencies.sort()
	agencies.insert(0, 'all agencies')
	domaintypes = list(domaintypemap.keys())
	domaintypes.sort()
	domaintypes.insert(0, 'all Types/Branches')

	agency = request.GET.get('agency')
	if agency == None:
		agency = 'all agencies'

	domaintype = request.GET.get('domaintype')
	if domaintype == None:
		domaintype = 'all Types/Branches'

	# search in ES for versions that have been detected
	s = Search(using=es, index=index).query().source(['data.uswdsversion'])
	versionmap = {}
	for i in s.scan():
			if isinstance(i.data.uswdsversion, str) and i.data.uswdsversion != '':
			    versionmap[i.data.uswdsversion] = 1
	versions = list(versionmap.keys())
	versions.sort()
	versions.insert(0, 'detected versions')
	versions.insert(0, 'all versions')

	version = request.GET.get('version')
	if version == None:
		version = 'all versions'

	# the query should be a number that we are comparing to total_score
	query = request.GET.get('q')
	try:
		query = int(query)
	except:
		query = 0

	# do the actual query here.
	s = Search(using=es, index=index)
	s = s.query(Bool(should=[Range(data__total_score={'gte': query})]))
	if version != 'all versions':
		if version == 'detected versions':
			s = s.query("query_string", query='v*', fields=['data.uswdsversion'])
		else:
			versionquery = '"' + version + '"'
			s = s.query("query_string", query=versionquery, fields=['data.uswdsversion'])
	if agency != 'all agencies':
		agencyquery = '"' + agency + '"'
		s = s.query("query_string", query=agencyquery, fields=['agency'])
	if domaintype != 'all Types/Branches':
		domaintypequery = '"' + domaintype + '"'
		s = s.query("query_string", query=domaintypequery, fields=['domaintype'])

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

	context = {
		'search_results': results.hits,
		'dates': dates,
		'query': query,
		'selected_date': date,
		'page_obj': page,
		'agencies': agencies,
		'selected_agency': agency,
		'domaintypes': domaintypes,
		'selected_domaintype': domaintype,
		'versions': versions,
		'selected_version': version,
	}

	return render(request, "searchUSWDS.html", context=context)
