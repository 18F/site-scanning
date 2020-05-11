import logging
import os
import re
from datetime import datetime

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range, Bool, Q


# This function generates an actual query given a kwarg set.
# The idea is that all the different kinds of views into the data can
# give different parameters to search the specified index and
# thus have a generalized query interface rather than having a harcdoded
# query for each view.
def getquery(index, present=None, agency=None, domaintype=None, query=None, org=None, sort=None, version=None, totalscorequery=None, mimetype=None, page=None, indexbase=None, statuscodelocation=None, domainsearch=None, displaytype=None):
    es = Elasticsearch([os.environ['ESURL']])
    s = Search(using=es, index=index)

    # This is so that we can do general queries.  If we don't specify one,
    # then find everything.
    if query is not None:
        s = s.query('simple_query_string', query=query)
    else:
        s = s.query(Q('match_all'))

    # This is getting complicated.  Present/not present may look different depending on the displaytype
    if displaytype == 'dap':
        if present == "DAP Present":
            presentquery = True
        elif present == "DAP Not Present":
            presentquery = False
        else:
            presentquery = '*'
        s = s.query("query_string", query=presentquery, fields=['data.dap_detected'])
    else:
        if present is not None and statuscodelocation is not None:
            if present == "Present":
                presentquery = '"200"'
            elif present == "Not Present":
                presentquery = '-"200"'
            else:
                presentquery = '*'
            s = s.query("query_string", query=presentquery, fields=[statuscodelocation])

    if agency != 'All Agencies' and agency is not None:
        agencyquery = '"' + agency + '"'
        s = s.query("query_string", query=agencyquery, fields=['agency'])

    if domaintype != 'All Branches' and domaintype is not None:
        domaintypequery = '"' + domaintype + '"'
        s = s.query("query_string", query=domaintypequery, fields=['domaintype'])

    if org != 'All Organizations' and org is not None:
        orgquery = '"' + org + '"'
        s = s.query("query_string", query=orgquery, fields=['organization'])

    if version != 'all versions' and version is not None:
        if version == 'detected versions':
            s = s.query("query_string", query='v*', fields=['data.uswdsversion'])
        else:
            versionquery = '"' + version + '"'
            s = s.query("query_string", query=versionquery, fields=['data.uswdsversion'])

    if totalscorequery is not None:
        s = s.query(Bool(should=[Range(data__total_score={'gte': totalscorequery})]))

    # this type of filter is tricky:  we need to filter on data that is
    # in another index.  The way we are doing this is by finding the list
    # of domains for the page we are interested in which have the mimetype
    # we want, and then filtering our query by that list.
    if mimetype is not None and page is not None and indexbase is not None:
        domains = []
        if mimetype != 'all content_types':
            mimetypequery = '"' + mimetype + '"'
            domains = domainsWith(page, 'content_type', mimetypequery, indexbase + '-pagedata')
            if len(domains) > 0:
                s = s.filter("terms", domain=domains)
            else:
                # no domains with the mimetype for this page found: reset to an empty query
                s = s.query(~Q('match_all'))

    if domainsearch is not None and domainsearch != 'None':
        dquery = '*' + domainsearch + '*'
        s = s.query("query_string", query=dquery, fields=['domain'])

    if sort is None:
        s = s.sort('domain')
    else:
        s = s.sort(sort)

    # # XXX debugging
    # print(s.to_dict())
    # print('count is', s.count())
    # print('index is', index)
    return s


# search in ES for the list of dates that are indexed
def get_dates():
    es = Elasticsearch([os.environ['ESURL']])
    indexlist = es.indices.get_alias().keys()
    datemap = {}
    for i in indexlist:
        a = i.split('-', maxsplit=3)
        date = '-'.join(a[0:3])
        if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}', date):
            datemap[date] = 1
    dates = list(datemap.keys())
    dates.sort(reverse=True)

    # If specified, omit today from results.
    # The use case for this is to omit potentially on-going, incomplete scans
    # dates from the frontend.
    # TODO: Revisit this logic, or the default behavior of the API.
    if settings.API_OMIT_TODAY:
        today = datetime.utcnow().date().isoformat()
        dates = [
            date
            for date in dates
            if date != today
        ]

    dates.insert(0, 'Scan Date')
    return dates


# search in ES for the unique values in a particular field
# If you call this on a field which is iterable, it will
# just give you the list, or the keys of the dictionary.
#
# If you call this with a subfield, it expects the field to
# be a dict and will get all the values from the specified
# subfield under every item.  This is so you can do things
# like find all mime_types under all the different pages.
#
# XXX seems like there ought to be a way to do this with aggregates in ES.
def get_list_from_fields(index, field, subfield=None):
    es = Elasticsearch([os.environ['ESURL']])
    s = Search(using=es, index=index).query().source([field])
    fieldlist = field.split('.')
    valueset = set()
    for i in s.scan():
        v = i.to_dict()
        for f in fieldlist:
            v = v[f]
        if isinstance(v, str) or not hasattr(v, '__iter__'):
            valueset.add(v)
        else:
            for z in list(v):
                if subfield is None:
                    valueset.add(z)
                else:
                    valueset.add(v[z][subfield])
    values = list(valueset)
    try:
        values.sort()
    except TypeError:
        print('warning:  cannot sort list with varying types from field:', field, 'subfield:', str(subfield), 'index:', index)
    return values


# Periods in fields are illegal, so we use this function to fix this.
def deperiodize(mystring):
    if mystring is None:
        return None
    else:
        return re.sub(r'\.', '//', mystring)


# Periods in fields are illegal, so we use this function to get proper names back.
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
    es = Elasticsearch([os.environ['ESURL']])
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


# mix in data from another scan in.
def mixpagedatain(scan, indexbase, indextype='pagedata'):
    es = Elasticsearch([os.environ['ESURL']])
    suffix = '-' + indextype
    s = Search(using=es, index=indexbase + suffix).filter('terms', domain=[scan['domain']])
    try:
        for i in s.scan():
            scan['extradata'] = i.data.to_dict()
    except IndexError:
        logging.error('could not find pagedata index for mixing pagedata in')
    return scan


# build a popup item that we can pass on to the search200.html template
def popupbuilder(name, valuelist, disabled=False, selectedvalue=''):
    if disabled is True:
        popup = {'name': name, 'disabled': 'disabled', 'values': {}}
    else:
        popup = {'name': name, 'disabled': '', 'values': {}}

    for i in valuelist:
        if i == selectedvalue:
            popup['values'][i] = 'selected'
        else:
            popup['values'][i] = ''
    return popup


# function to set the displaytypetitle up.
def setdisplaytypetitle(displaytype):
    displaytypetitle = '200 Scans Search'

    if displaytype == '200-developer':
        displaytypetitle = 'api.data.gov Search'
    elif displaytype == '200-codejson':
        displaytypetitle = 'code.gov Scan Search'
    elif displaytype == '200-data.json':
        displaytypetitle = 'data.gov Scan Search'
    elif displaytype == '200-robotstxt':
        displaytypetitle = 'robots.txt Scan Search'
    elif displaytype == 'dap':
        displaytypetitle = 'DAP Scan Search'
    elif displaytype == 'third_parties':
        displaytypetitle = 'Third Party Services Search'

    return displaytypetitle
