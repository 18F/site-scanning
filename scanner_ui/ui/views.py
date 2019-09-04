from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
import os
import datetime
import logging
import re
import json
import csv
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range, Bool, Q

# Create your views here.

es = Elasticsearch([os.environ['ESURI']])


# search in ES for the list of dates that are indexed
def getdates():
	es = Elasticsearch([os.environ['ESURI']])
	indexlist = es.indices.get_alias().keys()
	datemap = {}
	for i in indexlist:
		a = i.split('-', maxsplit=3)
		date = '-'.join(a[0:3])
		datemap[date] = 1
	dates = list(datemap.keys())
	dates.sort(reverse=True)
	dates.insert(0, 'Scan Date')
	return dates


def about(request):
	# This is just to show how to get data from python into the page.
	# You could just edit the template directly to add this static text
	# too.
	info = 'Hello world!'

	context = {
		'info': info,
	}
	return render(request, "about.html", context=context)

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


# Periods in fields are now illegal, so we use this function to fix this.
def deperiodize(mystring):
	if mystring == None:
		return None
	else:
		return re.sub(r'\.', '//', mystring)


# Periods in fields are now illegal, so we use this function to get proper names back.
def periodize(mystring):
	if mystring == None:
		return None
	else:
		return re.sub(r'\/\/', '.', mystring)	


# Slashes in values need to be escaped
def deslash(mystring):
	if mystring == None:
		return None
	else:
		return re.sub(r'\/', '\/', mystring)


# This function is meant to search the pagedata index for domains
# which have page data that match the key/value supplied and return
# the list to the caller.
def domainsWith(page, key, value, index):
	fielddata = [
		'data.*.content_type',
		'domain'
	]
	searchfields = ['data.' + deperiodize(page) + '.' + key]
	s = Search(using=es, index=index)
	s = s.query("query_string", query=deslash(value), fields=searchfields)
	s = s.source(fielddata)
	domainmap = {}
	try:
		for i in s.scan():
			domainmap[i.domain] = 1
	except:
		logging.error('error searching for domains in index: ' + index)
	domains = list(domainmap.keys())
	return list(domainmap.keys())


# This function generates the actual 200 scanner query
def get200query(indexbase, my200page, agency, domaintype, org, mimetype, query):
	index = indexbase + '-200scanner'
	s = Search(using=es, index=index)
	s = s.sort('domain')
	if query == None:
		# produce an empty query
		s = s.query(~Q('match_all'))
	else:
		if my200page == 'All Scans':
			s = s.query("simple_query_string", query=query)
		else:
			field = 'data.' + deperiodize(my200page)
			s = s.query("query_string", query=query, fields=[field])
		if agency != 'All Agencies' and agency != None:
			s = s.filter("term", agency=agency)
		if domaintype != 'All Branches' and domaintype != None:
			s = s.filter("term", domaintype=domaintype)
		if org != 'All Organizations' and org != None:
			s = s.filter("term", organization=org)

		# filter with data derived from the pagedata index (if needed)
		pagedatadomains = []
		if mimetype != 'all content_types':
			domains = domainsWith(my200page, 'content_type', mimetype, indexbase + '-pagedata')
			pagedatadomains.extend(domains)
		if len(pagedatadomains) > 0:
			s = s.filter("terms", domain=pagedatadomains)

	return s


# mix in the pagedata scan in.
def mixpagedatain(scan, indexbase):
	s = Search(using=es, index=indexbase + '-pagedata').filter('terms', domain=[scan['domain']])
	try:
		for i in s.scan():
			scan['pagedata'] = i.data.to_dict()
	except:
		logging.error('could not find pagedata index for mixing pagedata in')
	return scan


def search200json(request):
	my200page = request.GET.get('200page')
	date = request.GET.get('date')
	agency = request.GET.get('agency')
	domaintype = request.GET.get('domaintype')
	mimetype = request.GET.get('mimetype')
	query = request.GET.get('q')
	org = request.GET.get('org')

	if my200page == None:
		my200page = 'All Scans'

	dates = getdates()
	indexbase = ''
	if date == 'None' or date == 'Scan Date' or date == None:
		indexbase = dates[1]
	else:
		indexbase = date

	s = get200query(indexbase, my200page, agency, domaintype, org, mimetype, query)
	response = HttpResponse(content_type='application/json')
	response['Content-Disposition'] = 'attachment; filename="200scan.json"'

	# write out a valid json array
	response.write('[')
	count = s.count()
	for i in s.scan():
		scan = i.to_dict()
		scandata = scan['data']

		# keys cannot have . in them, so do this to make it look proper
		del scan['data']
		scan['data'] = {}
		for k,v in scandata.items():
			scan['data'][periodize(k)] = v

		# mix in pagedata scan if we can
		if my200page != 'All Scans':
			scan = mixpagedatain(scan, indexbase)
			pagedata = scan['pagedata']

			# keys cannot have . in them, so do this to make it look proper
			del scan['pagedata']
			scan['pagedata'] = {}
			for k,v in pagedata.items():
				scan['pagedata'][periodize(k)] = v

		response.write(json.dumps(scan))
		if count > 1:
			response.write(',')
		count = count - 1
	response.write(']')

	return response


def search200csv(request):
	my200page = request.GET.get('200page')
	date = request.GET.get('date')
	agency = request.GET.get('agency')
	domaintype = request.GET.get('domaintype')
	mimetype = request.GET.get('mimetype')
	query = request.GET.get('q')
	org = request.GET.get('org')

	if my200page == None:
		my200page = 'All Scans'

	dates = getdates()
	indexbase = ''
	if date == 'None' or date == 'Scan Date' or date == None:
		indexbase = dates[1]
	else:
		indexbase = date

	s = get200query(indexbase, my200page, agency, domaintype, org, mimetype, query)
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="200scan.csv"'

	r = s.execute()

	# pull the scan data out into the top level to make it look better
	firsthit = r.hits[0].to_dict()
	firsthit = mixpagedatain(firsthit, indexbase)
	fieldnames = list(firsthit.keys())
	fieldnames.remove('data')
	for k,v in firsthit['data'].items():
		fieldnames.append(periodize(k))
	if 'pagedata' in fieldnames:
		fieldnames.remove('pagedata')
		for k,v in firsthit['pagedata'].items():
			for field,value in v.items():
				fieldnames.append(periodize(k) + ' ' + field)

	writer = csv.DictWriter(response, fieldnames=fieldnames)
	writer.writeheader()

	for i in s.scan():
		scan = i.to_dict()

		# mix in pagedata scan if we can
		if my200page != 'All Scans':
			scan = mixpagedatain(scan, indexbase)

			# pull the page data out into the top level to make it look better
			pagedata = scan['pagedata']
			del scan['pagedata']
			for k,v in pagedata.items():
				for field,value in v.items():
					scan[periodize(k) + ' ' + field] = value

		# pull the scan data out into the top level to make it look better
		scandata = scan['data']
		del scan['data']
		for k,v in scandata.items():
			scan[periodize(k)] = v

		writer.writerow(scan)

	return response


def search200(request):
	dates = getdates()

	date = request.GET.get('date')
	if date == None or date == 'Scan Date':
		indexbase = dates[1]
	else:
		indexbase = date
	index = indexbase + '-200scanner'

	# search in ES for 200 pages we can select
	my200page = request.GET.get('200page')
	if my200page == None:
		my200page = 'All Scans'
	s = Search(using=es, index=index).query().params(terminate_after=1)
	pagemap = {}
	try:
		for i in s.scan():
				for z in i.data.to_dict().keys():
					pagemap[periodize(z)] = 1
		my200pages = list(pagemap.keys())
	except:
		my200pages = []
	my200pages.insert(0, 'All Scans')

	# get the agencies/domaintypes/orgs
	agencies = getListFromFields(index, 'agency')
	agencies.insert(0, 'All Agencies')
	domaintypes = getListFromFields(index, 'domaintype')
	domaintypes.insert(0, 'All Branches')
	orgs = getListFromFields(index, 'organization')
	orgs.insert(0, 'All Organizations')


	agency = request.GET.get('agency')
	if agency == None:
		agency = 'All Agencies'

	domaintype = request.GET.get('domaintype')
	if domaintype == None:
		domaintype = 'All Branches'

	org = request.GET.get('org')
	if org == None:
		org = 'All Organizations'

	# Find list of mime types from the pagedata index
	fielddata = [
		'data.*.content_type',
	]
	s = Search(using=es, index=indexbase + '-pagedata').query().source(fielddata)
	mimetypemap = {}
	try:
		for i in s.scan():
			for k,v in i.data.to_dict().items():
				mimetypemap[v['content_type']] = 1
	except:
		logging.error('could not find pagedata index to generate the mimetypemap')

	mimetype = request.GET.get('mimetype')
	if mimetype == None:
		mimetype = 'all content_types'
	mimetypes = list(mimetypemap.keys())
	mimetypes.sort()
	mimetypes.insert(0, 'all content_types')

	# find whether we want to do present/notpresent/all
	present = request.GET.get('present')
	if present == None:
			present = "Present"
	presentlist = [
		"Present",
		"Not Present",
		"All"
	]

	# do the actual query here.
	if present == 'Present':
		query = '"200"'
	elif present == 'Not Present':
		query = '-"200"'
	else:
		query = '*'
	s = get200query(indexbase, my200page, agency, domaintype, org, mimetype, query)

	# set up pagination here
	hitsperpagelist = ['20', '50', '100', '200']
	hitsperpage = request.GET.get('hitsperpage')
	if hitsperpage == None:
		hitsperpage = hitsperpagelist[1]
	page_no = request.GET.get('page')
	paginator = Paginator(s, int(hitsperpage))
	try:
		page = paginator.page(page_no)
	except PageNotAnInteger:
		page = paginator.page(1)
	except EmptyPage:
		page = paginator.page(paginator.num_pages)
	results = page.object_list.execute()

	# mix in the pagedata scan into the page we are displaying.
	pagedomainlist = []
	# get list of domains to search for in the pagedata index
	for i in results:
		pagedomainlist.insert(0, i.domain)
	s = Search(using=es, index=indexbase + '-pagedata').filter('terms', domain=pagedomainlist)
	pagedatastructure = {}
	# get data from pagedata index
	try:
		for i in s.scan():
			pagedatastructure[i.domain] = i.data.to_dict()
	except:
		logging.error('could not find pagedata index to create the pagedatastructure')

	# mix pagedata into results
	pagekeys = []
	if my200page != 'All Scans':
		for i in results:
			try:
				keys = list(pagedatastructure[i.domain][deperiodize(my200page)].keys())
				pagekeys = list(set().union(keys, pagekeys))
			except:
				logging.error('could not find pagedata to merge in for ' + i.domain)
	pagekeys.sort()
	for i in results:
		if my200page == 'All Scans':
			i['url'] = 'https://' + i.domain
			i['pagedata'] = []
		else:
			i['url'] = 'https://' + i.domain + my200page
			i['pagedata'] = []
			for k in pagekeys:
				try:
					i['pagedata'].append(pagedatastructure[i.domain][deperiodize(my200page)][k])
				except:
					i['pagedata'].append('')

	context = {
		'search_results': results.hits,
		'dates': dates,
		'query': query,
		'selected_date': date,
		'selected_200page': periodize(my200page),
		'my200pages': my200pages,
		'page_obj': page,
		'agencies': agencies,
		'selected_agency': agency,
		'domaintypes': domaintypes,
		'selected_domaintype': domaintype,
		'presentlist': presentlist,
		'selected_present': present,
		'mimetypes': mimetypes,
		'selected_mimetype': mimetype,
		'pagekeys': pagekeys,
		'hitsperpagelist': hitsperpagelist,
		'selected_hitsperpage': hitsperpage,
		'selected_org': org,
		'orglist': orgs,
	}

	return render(request, "search200.html", context=context)


def getUSWDSquery(indexbase, query, version, agency, domaintype):
	index = indexbase + '-uswds2'
	try:
		query = int(query)
	except:
		query = 0

	s = Search(using=es, index=index)
	s = s.sort('domain')
	s = s.query(Bool(should=[Range(data__total_score={'gte': query})]))
	if version != 'all versions':
		if version == 'detected versions':
			s = s.query("query_string", query='v*', fields=['data.uswdsversion'])
		else:
			versionquery = '"' + version + '"'
			s = s.query("query_string", query=versionquery, fields=['data.uswdsversion'])
	if agency != 'All Agencies':
		agencyquery = '"' + agency + '"'
		s = s.query("query_string", query=agencyquery, fields=['agency'])
	if domaintype != 'All Branches':
		domaintypequery = '"' + domaintype + '"'
		s = s.query("query_string", query=domaintypequery, fields=['domaintype'])

	return s


def searchUSWDSjson(request):
	date = request.GET.get('date')
	version = request.GET.get('version')
	query = request.GET.get('q')
	agency = request.GET.get('agency')
	domaintype = request.GET.get('domaintype')

	dates = getdates()
	indexbase = ''
	if date == 'None' or date == 'Scan Date' or date == None:
		indexbase = dates[1]
	else:
		indexbase = date

	s = getUSWDSquery(indexbase, query, version, agency, domaintype)
	response = HttpResponse(content_type='application/json')
	response['Content-Disposition'] = 'attachment; filename="USWDSscan.json"'

	# write out a valid json array
	response.write('[')
	count = s.count()
	for i in s.scan():
		scan = i.to_dict()
		response.write(json.dumps(i.to_dict()))
		if count > 1:
			response.write(',')
		count = count - 1
	response.write(']')

	return response


def searchUSWDScsv(request):
	date = request.GET.get('date')
	version = request.GET.get('version')
	query = request.GET.get('q')
	agency = request.GET.get('agency')
	domaintype = request.GET.get('domaintype')

	dates = getdates()
	indexbase = ''
	if date == 'None' or date == 'Scan Date' or date == None:
		indexbase = dates[1]
	else:
		indexbase = date

	s = getUSWDSquery(indexbase, query, version, agency, domaintype)
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="USWDSscan.csv"'

	r = s.execute()

	# pull the scan data out into the top level to make it look better
	try:
		firsthit = r.hits[0].to_dict()
		fieldnames = list(firsthit.keys())
		fieldnames.remove('data')
		for k,v in firsthit['data'].items():
			fieldnames.append(k)

		writer = csv.DictWriter(response, fieldnames=fieldnames)
		writer.writeheader()

		for i in s.scan():
			scan = i.to_dict()

			# pull the scan data out into the top level to make it look better
			scandata = scan['data']
			del scan['data']
			for k,v in scandata.items():
				scan[k] = v

			writer.writerow(scan)
	except:
		writer = csv.writer(response)
		writer.writerow(['No Data'])

	return response


# search in ES for the unique values in a particular field
def getListFromFields(index, field):
	es = Elasticsearch([os.environ['ESURI']])
	s = Search(using=es, index=index).query().source([field])
	valuemap = {}
	try:
		for i in s.scan():
		        valuemap[i[field]] = 1
		values = list(valuemap.keys())
		values.sort()
	except:
		values = []
	return values


def searchUSWDS(request):
	dates = getdates()

	date = request.GET.get('date')
	if date == None or date == 'Scan Date':
		indexbase = dates[1]
	else:
		indexbase = date
	index = indexbase + '-uswds2'

	# get the agencies/domaintypes
	agencies = getListFromFields(index, 'agency')
	agencies.insert(0, 'All Agencies')
	domaintypes = getListFromFields(index, 'domaintype')
	domaintypes.insert(0, 'All Branches')

	agency = request.GET.get('agency')
	if agency == None:
		agency = 'All Agencies'

	domaintype = request.GET.get('domaintype')
	if domaintype == None:
		domaintype = 'All Branches'

	# search in ES for versions that have been detected
	s = Search(using=es, index=index).query().source(['data.uswdsversion'])
	versionmap = {}
	try:
		for i in s.scan():
				if isinstance(i.data.uswdsversion, str) and i.data.uswdsversion != '':
				    versionmap[i.data.uswdsversion] = 1
		versions = list(versionmap.keys())
		versions.sort()
	except:
		versions = []
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
	s = getUSWDSquery(indexbase, query, version, agency, domaintype)

	# set up pagination here
	hitsperpagelist = ['20', '50', '100', '200']
	hitsperpage = request.GET.get('hitsperpage')
	if hitsperpage == None:
		hitsperpage = hitsperpagelist[1]
	page_no = request.GET.get('page')
	paginator = Paginator(s, int(hitsperpage))
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
		'hitsperpagelist': hitsperpagelist,
		'selected_hitsperpage': hitsperpage,
	}

	return render(request, "searchUSWDS.html", context=context)
