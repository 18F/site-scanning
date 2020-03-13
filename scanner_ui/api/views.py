from rest_framework import viewsets, pagination
from rest_framework.response import Response
from .serializers import ScanSerializer
import os
from scanner_ui.ui.views import getdates, getListFromFields
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range
import re
from collections import OrderedDict

# Create your views here.


# we need this because AttrDict is used all over by elasticsearch_dsl,
# and it can't do .items().  So we will wrap it.
class ItemsWrapper(OrderedDict):
    def __init__(self, s):
        self.s = s

    def __iter__(self):
        for hit in self.s.scan():
            yield hit.to_dict()

    def __len__(self):
        return self.s.count()

    def __getitem__(self, index):
        return self.s[index]

    def __str__(self):
        return str(self.s.to_dict())


# get all the scans of the type and domain specified from ES.  If the type is
# None, you get all of that scantype.  If the domain is None, you
# get all domains.  If you supply a request, set the API url up
# for the scan using it.
def getScansFromES(scantype=None, domain=None, request=None, excludeparams=None, date=None):
    es = Elasticsearch([os.environ['ESURL']])
    dates = getdates()
    if date is None or date not in dates:
        date = dates[1]
    selectedindex = date + '-*'
    indices = list(es.indices.get_alias(selectedindex).keys())
    y, m, d, scantypes = zip(*(s.split("-") for s in indices))
    if excludeparams is None:
        excludeparams = []

    # if we have a valid scantype, then search that
    if scantype in scantypes:
        index = date + '-' + scantype
        s = Search(using=es, index=index)
    else:
        s = Search(using=es, index=selectedindex)

    # This is to handle queries
    # arguments should be like ?domain=gsa*&data.foo=bar&numberfield=gt:50&numberfield=lt:20
    # arguments are ANDed together
    for k, v in request.GET.items():
        # don't try to search on excluded parameters
        if k in excludeparams:
            next

        # find greater/lesserthan queries
        elif re.match(r'^gt:[0-9]+', v):
            gt = v.split(':')[1]
            q = Range(**{k: {'gt': gt}})
            s = s.query(q)
        elif re.match(r'^lt:[0-9]+', v):
            lt = v.split(':')[1]
            q = Range(**{k: {'lt': lt}})
            s = s.query(q)

        # everything else, just try searching for!
        else:
            s = s.query("query_string", query=v, fields=[k])

    s = s.sort('domain')

    # filter by domain if we have one
    if domain is not None:
        s = s.filter("term", domain=domain)

    # # XXX
    # print(s.to_dict())

    return ItemsWrapper(s)


# get the list of scantypes by scraping the indexes
def getscantypes(date=None):
    es = Elasticsearch([os.environ['ESURL']])
    dates = getdates()
    if date is None:
        date = dates[1]
    selectedindex = date + '-*'
    indices = list(es.indices.get_alias(selectedindex).keys())
    y, m, d, scantypes = zip(*(s.split("-") for s in indices))
    return scantypes


class ElasticsearchPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        page_number = int(request.query_params.get(self.page_query_param, 1))

        paginator = self.django_paginator_class(queryset, page_size)
        self.page = paginator.page(page_number)
        self.request = request

        start = page_size * (page_number - 1)
        finish = start + page_size

        qs = ItemsWrapper(queryset[start:finish])
        return qs


class DomainsViewset(viewsets.GenericViewSet):
    serializer_class = ScanSerializer
    pagination_class = ElasticsearchPagination

    def get_queryset(self, domain=None, date=None):
        pageparams = [self.pagination_class.page_query_param, self.pagination_class.page_size_query_param]
        if self.pagination_class.page_query_param in self.request.GET:
            return getScansFromES(request=self.request, domain=domain, excludeparams=pageparams, date=date)
        else:
            return getScansFromES(request=self.request, domain=domain, date=date)

    def list(self, request, date=None):
        scans = self.get_queryset(date=date)

        # if we are requesting pagination, then give it
        if self.pagination_class.page_query_param in request.GET:
            pageqs = self.paginate_queryset(scans)
            if pageqs is not None:
                page = []
                for hit in pageqs.s.execute():
                    page.append(hit.to_dict())
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        # otherwise, return the full dataset
        serializer = self.get_serializer(scans, many=True)
        return Response(serializer.data)

    def retrieve(self, request, domain=None, date=None):
        scans = self.get_queryset(domain=domain, date=date)
        serializer = self.get_serializer(scans, many=True)
        return Response(serializer.data)


class ScansViewset(viewsets.GenericViewSet):
    serializer_class = ScanSerializer
    pagination_class = ElasticsearchPagination

    def get_queryset(self, scantype=None, domain=None, date=None):
        pageparams = [self.pagination_class.page_query_param, self.pagination_class.page_size_query_param]
        if self.pagination_class.page_query_param in self.request.GET:
            return getScansFromES(request=self.request, domain=domain, scantype=scantype, excludeparams=pageparams, date=date)
        else:
            return getScansFromES(request=self.request, domain=domain, scantype=scantype, date=date)

    def list(self, request, date=None):
        scans = getscantypes(date=date)
        return Response(scans)

    def retrieve(self, request, scantype=None, date=None):
        scans = self.get_queryset(scantype=scantype, date=date)

        # if we are requesting pagination, then give it
        if self.pagination_class.page_query_param in request.GET:
            pageqs = self.paginate_queryset(scans)
            if pageqs is not None:
                page = []
                for hit in pageqs.s.execute():
                    page.append(hit.to_dict())
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(scans, many=True)
        return Response(serializer.data)

    def scan(self, request, scantype=None, domain=None, date=None):
        scan = self.get_queryset(scantype=scantype, domain=domain, date=date)
        if len(scan) != 1:
            raise Exception('too many or too few scans', scan)
        serializer = self.get_serializer(scan[0].execute().hits[0].to_dict())
        return Response(serializer.data)


# This gets all the unique values for a field
def uniquevalues(date=None, scantype=None, field=None, subfield=None):
    if date is None:
        # default to most recent date
        date = getdates()[1]

    if scantype is None:
        raise Exception('no scantype specified')

    index = date + '-' + scantype
    things = getListFromFields(index, field, subfield=subfield)
    return things


class ListsViewset(viewsets.GenericViewSet):
    queryset = ''

    def dates(self, request):
        dates = getdates()[1:]
        return Response(dates)

    def agencies(self, request, scantype=None, date=None):
        agencies = uniquevalues(date=date, scantype=scantype, field='agency')
        return Response(agencies)

    def domaintypes(self, request, scantype=None, date=None):
        domaintypes = uniquevalues(date=date, scantype=scantype, field='domaintype')
        return Response(domaintypes)

    def fieldvalues(self, request, date=None, scantype=None, field=None, subfield=None):
        if field is None:
            raise Exception('no field specified')
        things = uniquevalues(date=date, scantype=scantype, field=field, subfield=subfield)
        return Response(things)
