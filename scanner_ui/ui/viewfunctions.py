import os
import logging
import re
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range, Bool, Q


# This function generates an actual query given a kwarg set.
# The idea is that all the different kinds of views into the data can
# give different parameters to search the specified index and
# thus have a generalized query interface rather than having a harcdoded
# query for each view.
def getquery(index, present=None, agency=None, domaintype=None, query=None, org=None, sort=None, version=None, totalscorequery=None, mimetype=None, page=None, indexbase=None, statuscodelocation=None):
    es = Elasticsearch([os.environ['ESURL']])
    s = Search(using=es, index=index)

    # This is so that we can do general queries.  If we don't specify one,
    # then find everything.
    if query is not None:
        s = s.query('simple_query_string', query=query)
    else:
        s = s.query(Q('match_all'))

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
            domains = domainsWith(page, 'content_type', mimetype, indexbase + '-pagedata')
        if len(domains) > 0:
            s = s.filter("terms", domain=domains)

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
def getdates():
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
    dates.insert(0, 'Scan Date')
    return dates


# search in ES for the unique values in a particular field
def getListFromFields(index, field, subfield=None):
    es = Elasticsearch([os.environ['ESURL']])
    s = Search(using=es, index=index).query().source([field])
    valuemap = {}
    try:
        for i in s.scan():
            if subfield is None:
                valuemap[i[field]] = 1
            else:
                for k, v in i[field].to_dict().items():
                    valuemap[v[subfield]] = 1
        values = list(valuemap.keys())
    except:
        values = []
    values.sort()
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


# mix in the pagedata scan in.
def mixpagedatain(scan, indexbase):
    es = Elasticsearch([os.environ['ESURL']])
    s = Search(using=es, index=indexbase + '-pagedata').filter('terms', domain=[scan['domain']])
    try:
        for i in s.scan():
            scan['pagedata'] = i.data.to_dict()
    except IndexError:
        logging.error('could not find pagedata index for mixing pagedata in')
    return scan
