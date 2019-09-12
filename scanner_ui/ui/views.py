from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
import os
import logging
import re
import json
import csv
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range, Bool, Q
from django.urls import reverse


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
    if mystring is None:
        return None
    else:
        return re.sub(r'\.', '//', mystring)


# Periods in fields are now illegal, so we use this function to get proper names back.
def periodize(mystring):
    if mystring is None:
        return None
    else:
        return re.sub(r'\/\/', '.', mystring)


# Slashes in values need to be escaped
def deslash(mystring):
    if mystring is None:
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
    except IndexError:
        logging.error('error searching for domains in index: ' + index)
    return list(domainmap.keys())


# This function generates the actual 200 scanner query
def get200query(indexbase, my200page, agency, domaintype, org, mimetype, query):
    index = indexbase + '-200scanner'
    s = Search(using=es, index=index)
    s = s.sort('domain')

    if query is None:
        # produce an empty query
        s = s.query(~Q('match_all'))
    else:
        if my200page == 'All Scans':
            s = s.query('simple_query_string', query=query)
        else:
            field = 'data.' + deperiodize(my200page)
            s = s.query('query_string', query=query, fields=[field])

        if agency != 'All Agencies' and agency is not None:
            agencyquery = '"' + agency + '"'
            s = s.query("query_string", query=agencyquery, fields=['agency'])
        if domaintype != 'All Branches' and domaintype is not None:
            domaintypequery = '"' + domaintype + '"'
            s = s.query("query_string", query=domaintypequery, fields=['domaintype'])
        if org != 'All Organizations' and org is not None:
            orgquery = '"' + org + '"'
            s = s.query("query_string", query=orgquery, fields=['organization'])

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
    except IndexError:
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

    if my200page is None:
        my200page = 'All Scans'

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
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
        for k, v in scandata.items():
            scan['data'][periodize(k)] = v

        # mix in pagedata scan if we can
        if my200page != 'All Scans':
            scan = mixpagedatain(scan, indexbase)
            pagedata = scan['pagedata']

            # keys cannot have . in them, so do this to make it look proper
            del scan['pagedata']
            scan['pagedata'] = {}
            for k, v in pagedata.items():
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

    if my200page is None:
        my200page = 'All Scans'

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
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
    for k, v in firsthit['data'].items():
        fieldnames.append(periodize(k))
    if 'pagedata' in fieldnames:
        fieldnames.remove('pagedata')
        for k, v in firsthit['pagedata'].items():
            for field, value in v.items():
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
            for k, v in pagedata.items():
                for field, value in v.items():
                    scan[periodize(k) + ' ' + field] = value

        # pull the scan data out into the top level to make it look better
        scandata = scan['data']
        del scan['data']
        for k, v in scandata.items():
            scan[periodize(k)] = v

        writer.writerow(scan)

    return response


def search200(request, displaytype=None):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-200scanner'

    # search in ES for 200 pages we can select
    my200page = request.GET.get('200page')
    if my200page is None:
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
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    org = request.GET.get('org')
    if org is None:
        org = 'All Organizations'

    # Find list of mime types from the pagedata index
    fielddata = [
        'data.*.content_type',
    ]
    s = Search(using=es, index=indexbase + '-pagedata').query().source(fielddata)
    mimetypemap = {}
    try:
        for i in s.scan():
            for k, v in i.data.to_dict().items():
                mimetypemap[v['content_type']] = 1
    except:
        logging.error('could not find pagedata index to generate the mimetypemap')

    mimetype = request.GET.get('mimetype')
    if mimetype is None:
        mimetype = 'all content_types'
    mimetypes = list(mimetypemap.keys())
    mimetypes.sort()
    mimetypes.insert(0, 'all content_types')

    # find whether we want to do present/notpresent/all
    present = request.GET.get('present')
    if present is None:
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
    if hitsperpage is None:
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

    # create columns for us to render in the page
    columns = []

    # set some defaults for use while looping
    selectedpage = deperiodize(my200page)
    displaytypetitle = '200 Scans Search'

    for i in results:
        # Below here are where you can set up different types of pages.
        # Just create another 'elif displaytype == "yourpagetype"' section below
        # and do what the other displaytypes do:  create a column, add your data
        # to it, store it in the results and set the columns and page title.
        #
        # XXX seems like there ought to be a more clever way to do this.
        #     I'm definitely not DRY here.

        # 200-dev style display
        if displaytype == '200-developer':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in pagedatastructure and my200page != 'All Scans':
                column['Final URL'] = pagedatastructure[i.domain][selectedpage]['final_url']
                column['Content Type'] = pagedatastructure[i.domain][selectedpage]['content_type']
                column['File Size (B)'] = pagedatastructure[i.domain][selectedpage]['content_length']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['File Size (B)'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())
            displaytypetitle = 'api.data.gov Search'

        # 200-codejson style display
        elif displaytype == '200-codejson':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in pagedatastructure and my200page != 'All Scans':
                column['Final URL'] = pagedatastructure[i.domain][selectedpage]['final_url']
                column['Content Type'] = pagedatastructure[i.domain][selectedpage]['content_type']
                column['json Items'] = pagedatastructure[i.domain][selectedpage]['json_items']
                column['File Size (B)'] = pagedatastructure[i.domain][selectedpage]['content_length']
                column['Code.gov Measurement Type'] = pagedatastructure[i.domain][selectedpage]['codegov_measurementtype']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['json Items'] = ''
                column['File Size (B)'] = ''
                column['Code.gov Measurement Type'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())
            displaytypetitle = 'code.gov Scan Search'

        # 200-data.json style display
        elif displaytype == '200-data.json':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in pagedatastructure and my200page != 'All Scans':
                column['Final URL'] = pagedatastructure[i.domain][selectedpage]['final_url']
                column['Content Type'] = pagedatastructure[i.domain][selectedpage]['content_type']
                column['json Items'] = pagedatastructure[i.domain][selectedpage]['json_items']
                column['File Size (B)'] = pagedatastructure[i.domain][selectedpage]['content_length']
                column['Opendata Conformity'] = pagedatastructure[i.domain][selectedpage]['opendata_conforms_to']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['json Items'] = ''
                column['File Size (B)'] = ''
                column['Opendata Conformity'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())
            displaytypetitle = 'data.gov Scan Search'

        # 200-robotstxt style display
        elif displaytype == '200-robotstxt':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in pagedatastructure and my200page != 'All Scans':
                column['Final URL'] = pagedatastructure[i.domain][selectedpage]['final_url']
                column['Content Type'] = pagedatastructure[i.domain][selectedpage]['content_type']
                column['File Size (B)'] = pagedatastructure[i.domain][selectedpage]['content_length']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['File Size (B)'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())
            displaytypetitle = 'robots.txt Scan Search'

        # default to the basic 200 scans search
        else:
            column = {}
            if my200page == 'All Scans':
                column['Domain'] = 'https://' + i.domain
            else:
                column['Domain'] = 'https://' + i.domain + my200page
            column['Branch'] = i.domaintype
            column['Agency'] = i.agency
            if my200page == 'All Scans':
                column['Response Code'] = ''
            else:
                column['Response Code'] = i.data[selectedpage]
            if i.domain in pagedatastructure and my200page != 'All Scans':
                column['File Size (B)'] = pagedatastructure[i.domain][selectedpage]['content_length']
                column['Content Type'] = pagedatastructure[i.domain][selectedpage]['content_type']
                column['Final URL'] = pagedatastructure[i.domain][selectedpage]['final_url']
                column['json Items'] = pagedatastructure[i.domain][selectedpage]['json_items']
                column['Opendata Conformity'] = pagedatastructure[i.domain][selectedpage]['opendata_conforms_to']
                column['Code.gov Measurement Type'] = pagedatastructure[i.domain][selectedpage]['codegov_measurementtype']
            else:
                column['File Size (B)'] = ''
                column['Content Type'] = ''
                column['Final URL'] = ''
                column['json Items'] = ''
                column['Opendata Conformity'] = ''
                column['Code.gov Measurement Type'] = ''
            detailpath = reverse('domains-detail', kwargs={'domain': i.domain})
            column['Other Scan Results'] = request.build_absolute_uri(detailpath)
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())
            if displaytype == None or displaytype == 'None':
                displaytypetitle = '200 Scans Search'
            else:
                # We should never hit this, but if we do, we will still display a page, and the displaytype will help us debug.
                displaytypetitle = '200 Scans Search: ' + displaytype

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
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'selected_org': org,
        'orglist': orgs,
        'columns': columns,
        'displaytype': displaytype,
        'displaytypetitle': displaytypetitle,
    }

    return render(request, "search200.html", context=context)


def getUSWDSquery(indexbase, query, version, agency, domaintype, sort):
    index = indexbase + '-uswds2'
    try:
        query = int(query)
    except:
        query = 0

    s = Search(using=es, index=index)
    if sort == 'Score':
        s = s.sort('-data.total_score')
    else:
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
    sort = request.GET.get('sort')

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date

    s = getUSWDSquery(indexbase, query, version, agency, domaintype, sort)
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="USWDSscan.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
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
    sort = request.GET.get('sort')

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date

    s = getUSWDSquery(indexbase, query, version, agency, domaintype, sort)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="USWDSscan.csv"'

    r = s.execute()

    # pull the scan data out into the top level to make it look better
    try:
        firsthit = r.hits[0].to_dict()
        fieldnames = list(firsthit.keys())
        fieldnames.remove('data')
        for k, v in firsthit['data'].items():
            fieldnames.append(k)

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        for i in s.scan():
            scan = i.to_dict()

            # pull the scan data out into the top level to make it look better
            scandata = scan['data']
            del scan['data']
            for k, v in scandata.items():
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
    except:
        values = []
    values.sort()
    return values


def searchUSWDS(request):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
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
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    sort = request.GET.get('sort')
    if sort is None:
        sort = 'Domain'
    sortinglist = ['Domain', 'Score']

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
    # versions = getListFromFields(index, 'data.uswdsversion')
    versions.insert(0, 'detected versions')
    versions.insert(0, 'all versions')

    version = request.GET.get('version')
    if version is None:
        version = 'all versions'

    # the query should be a number that we are comparing to total_score
    query = request.GET.get('q')
    try:
        query = int(query)
    except:
        query = 0

    # do the actual query here.
    s = getUSWDSquery(indexbase, query, version, agency, domaintype, sort)

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
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
        'sortinglist': sortinglist,
        'selected_sort': sort,
    }

    return render(request, "searchUSWDS.html", context=context)


# This function generates the actual 200 scanner query
def getquery(index, present=None, agency=None, domaintype=None, query=None, org=None, sort=None):
    s = Search(using=es, index=index)

    if present is not None:
        if present == "Present":
            presentquery = '"200"'
        elif present == "Not Present":
            presentquery = '-"200"'
        else:
            presentquery = '*'
        s = s.query("query_string", query=presentquery, fields=['data.status_code'])

    if agency != 'All Agencies' and agency is not None:
        agencyquery = '"' + agency + '"'
        s = s.query("query_string", query=agencyquery, fields=['agency'])

    if domaintype != 'All Branches' and domaintype is not None:
        domaintypequery = '"' + domaintype + '"'
        s = s.query("query_string", query=domaintypequery, fields=['domaintype'])

    if org != 'All Organizations' and org is not None:
        orgquery = '"' + org + '"'
        s = s.query("query_string", query=orgquery, fields=['organization'])

    if query is None:
        # find everything
        s = s.query(Q('match_all'))
    else:
        s = s.query('simple_query_string', query=query)

    if sort is None:
        s = s.sort('domain')
    else:
        s = s.sort(sort)

    return s


def privacy(request):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-privacy'

    # get the agencies/domaintypes
    agencies = getListFromFields(index, 'agency')
    agencies.insert(0, 'All Agencies')
    domaintypes = getListFromFields(index, 'domaintype')
    domaintypes.insert(0, 'All Branches')

    agency = request.GET.get('agency')
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    # find whether we want to do present/notpresent/all
    present = request.GET.get('present')
    if present is None:
        present = "Present"
    presentlist = [
        "Present",
        "Not Present",
        "All"
    ]

    # do the actual query here.
    s = getquery(index, present=present, agency=agency, domaintype=domaintype)

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
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

    # process the search results on the page so that we can format them properly
    columns = []
    for i in results:
        column = {}
        column['Domain'] = i.domain
        column['Agency'] = i.agency
        column['Organization'] = i.organization
        column['Branch'] = i.domaintype
        column['Target URL'] = 'https://' + i.domain + '/privacy'
        if i.data['status_code'] == "200":
            column['Status'] = "Is Present"
        else:
            column['Status'] = "Not Present"
        column['Response Code'] = i.data['status_code']
        column['Final URL'] = i.data['final_url']
        column['Emails'] = i.data['emails']
        column['H1 Headers'] = i.data['h1']
        column['H2 Headers'] = i.data['h2']
        column['H3 Headers'] = i.data['h3']
        # store the column in the result, also populate the columns now, since
        # the results seem to be a type of dictionary that doesn't respond to .keys()
        columns = list(column.keys())
        i['column'] = list(column.values())

    title = '/privacy Page'
    blurb = 'This page will let you view information about the various /privacy pages out there'
    context = {
        'search_results': results.hits,
        'columns': columns,
        'dates': dates,
        'selected_date': date,
        'page_obj': page,
        'agencies': agencies,
        'selected_agency': agency,
        'domaintypes': domaintypes,
        'selected_domaintype': domaintype,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'presentlist': presentlist,
        'selected_present': present,
        'title': title,
        'blurb': blurb,
        'mainurl': 'privacy',
        'jsonurl': 'privacyjson',
        'csvurl': 'privacycsv',
    }
    return render(request, "customsearchpage.html", context=context)


def privacyjson(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-privacy'
    else:
        index = date + '-privacy'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype)
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="PrivacyPageData.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
        response.write(json.dumps(i.to_dict()))
        if count > 1:
            response.write(',')
        count = count - 1
    response.write(']')

    return response


def privacycsv(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-privacy'
    else:
        index = date + '-privacy'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="PrivacyPageData.csv"'

    r = s.execute()

    # pull the scan data out into the top level to make it look better
    firsthit = r.hits[0].to_dict()
    fieldnames = list(firsthit.keys())
    fieldnames.remove('data')
    for k, v in firsthit['data'].items():
        fieldnames.append(k)

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()

    for i in s.scan():
        scan = i.to_dict()

        # pull the scan data out into the top level to make it look better
        scandata = scan['data']
        del scan['data']
        for k, v in scandata.items():
            scan[k] = v

        writer.writerow(scan)

    return response


def sitemap(request):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-sitemap'

    # get the agencies/domaintypes
    agencies = getListFromFields(index, 'agency')
    agencies.insert(0, 'All Agencies')
    domaintypes = getListFromFields(index, 'domaintype')
    domaintypes.insert(0, 'All Branches')

    agency = request.GET.get('agency')
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    # find whether we want to do present/notpresent/all
    present = request.GET.get('present')
    if present is None:
        present = "Present"
    presentlist = [
        "Present",
        "Not Present",
        "All"
    ]

    # do the actual query here.
    s = getquery(index, present=present, agency=agency, domaintype=domaintype)

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
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

    # process the search results on the page so that we can format them properly
    columns = []
    for i in results:
        column = {}
        column['Domain'] = i.domain
        column['Agency'] = i.agency
        column['Organization'] = i.organization
        column['Branch'] = i.domaintype
        column['Target URL'] = 'https://' + i.domain + '/sitemap.xml'
        if i.data['status_code'] == "200":
            column['Status'] = "Is Present"
        else:
            column['Status'] = "Not Present"
        column['Response Code'] = i.data['status_code']
        column['Final URL'] = i.data['final_url']
        column['URL Count'] = i.data['url_tag_count']
        column['Locations in robots.txt'] = ' '.join(i.data['sitemap_locations_from_robotstxt'])
        # store the column in the result, also populate the columns now, since
        # the results seem to be a type of dictionary that doesn't respond to .keys()
        columns = list(column.keys())
        i['column'] = list(column.values())

    title = 'Sitemap Page'
    blurb = 'This page will let you view information about the various /sitemap.xml pages out there'
    context = {
        'search_results': results.hits,
        'columns': columns,
        'dates': dates,
        'selected_date': date,
        'page_obj': page,
        'agencies': agencies,
        'selected_agency': agency,
        'domaintypes': domaintypes,
        'selected_domaintype': domaintype,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'presentlist': presentlist,
        'selected_present': present,
        'title': title,
        'blurb': blurb,
        'mainurl': 'sitemap',
        'jsonurl': 'sitemapjson',
        'csvurl': 'sitemapcsv',
    }
    return render(request, "customsearchpage.html", context=context)


def sitemapjson(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-sitemap'
    else:
        index = date + '-sitemap'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype)
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="sitemapData.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
        response.write(json.dumps(i.to_dict()))
        if count > 1:
            response.write(',')
        count = count - 1
    response.write(']')

    return response


def sitemapcsv(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-sitemap'
    else:
        index = date + '-sitemap'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sitemapData.csv"'

    r = s.execute()

    # pull the scan data out into the top level to make it look better
    firsthit = r.hits[0].to_dict()
    fieldnames = list(firsthit.keys())
    fieldnames.remove('data')
    for k, v in firsthit['data'].items():
        fieldnames.append(k)

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()

    for i in s.scan():
        scan = i.to_dict()

        # pull the scan data out into the top level to make it look better
        scandata = scan['data']
        del scan['data']
        for k, v in scandata.items():
            scan[k] = v

        writer.writerow(scan)

    return response
