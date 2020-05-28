"""
Site scanner API views
"""

import csv
import json
import os
import re
from collections import OrderedDict

from django.http import StreamingHttpResponse
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import Range
from rest_framework import viewsets, pagination
from rest_framework.response import Response

from scanner_ui.ui.views import get_dates, get_list_from_fields
from .serializers import ScanSerializer



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
def get_scans_from_ES(*, scantype=None, domain=None, request=None, excludeparams=None, date=None, raw=False):
    es = Elasticsearch([os.environ['ESURL']])
    dates = get_dates()

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

    if raw:
        return s
    else:
        return ItemsWrapper(s)


# get the list of scantypes by scraping the indexes
def get_scan_types(date=None):
    es = Elasticsearch([os.environ['ESURL']])
    dates = get_dates()
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
        try:
            page_number = int(request.query_params.get(self.page_query_param, 1))
            paginator = self.django_paginator_class(queryset, page_size)
            self.page = paginator.page(page_number)
            self.request = request

            start = page_size * (page_number - 1)
            finish = start + page_size

            qs = ItemsWrapper(queryset[start:finish])
            return qs
        except Exception:
            # return an empty search query
            es = Elasticsearch([os.environ['ESURL']])
            s = Search(using=es)
            return ItemsWrapper(s.query(~Q('match_all')))


class DomainsViewset(viewsets.GenericViewSet):
    serializer_class = ScanSerializer
    pagination_class = ElasticsearchPagination

    def get_queryset(self, domain=None, date=None):
        pageparams = [self.pagination_class.page_query_param, self.pagination_class.page_size_query_param]
        return get_scans_from_ES(request=self.request, domain=domain, excludeparams=pageparams, date=date)

    def list(self, request, date=None):
        scans = self.get_queryset(date=date)

        # paginate the query.  If we return the entire dataset, we run out of memory
        try:
            pageqs = self.paginate_queryset(scans)
            mypage = []
            for hit in pageqs.s.execute():
                mypage.append(hit.to_dict())
            serializer = self.get_serializer(mypage, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception:
            # there was nothing on the page, so...
            return Response([])

    def retrieve(self, request, domain=None, date=None):
        scans = self.get_queryset(domain=domain, date=date)
        serializer = self.get_serializer(scans, many=True)
        return Response(serializer.data)


class ScansViewset(viewsets.GenericViewSet):
    """
    Returns scan results for the provided scan type.
    """

    serializer_class = ScanSerializer
    pagination_class = ElasticsearchPagination

    def get_queryset(self, scantype=None, domain=None, date=None):
        pageparams = [self.pagination_class.page_query_param, self.pagination_class.page_size_query_param]
        return get_scans_from_ES(
            request=self.request,
            domain=domain,
            scantype=scantype,
            excludeparams=pageparams,
            date=date
        )

    def list(self, request, date=None):
        scans = get_scan_types(date=date)
        return Response(scans)

    def retrieve(self, request, scantype=None, date=None):
        scans = self.get_queryset(scantype=scantype, date=date)

        # paginate the query.  If we return the entire dataset, we run out of memory
        try:
            pageqs = self.paginate_queryset(scans)
            mypage = []
            for hit in pageqs.s.execute():
                mypage.append(hit.to_dict())
            serializer = self.get_serializer(mypage, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception:
            # there was nothing on the page, so...
            return StreamingHttpResponse([])

    def scan(self, request, scantype=None, domain=None, date=None):
        scan = self.get_queryset(scantype=scantype, domain=domain, date=date)
        if len(scan) != 1:
            raise Exception('too many or too few scans', scan)
        serializer = self.get_serializer(scan[0].execute().hits[0].to_dict())
        return Response(serializer.data)


# This is used for the csv writer used by the StreamingHttpResponse
class CSVEcho:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def flatten_dict(data, max_depth, depth=0):
    depth += 1

    if type(data) != dict:
        return data

    for key, value in list(data.items()):
        if type(value) == dict:
            if depth == max_depth:
                data[key] = json.dumps(value)
            else:
                flatten_dict(value, max_depth, depth=depth)
                data.pop(key)
                for key2, value2 in value.items():
                    data[f'{key}.{key2}'] = value2

    return data


def iter_items(scans, pseudo_buffer, headers, max_depth):
    writer = csv.DictWriter(pseudo_buffer, fieldnames=headers)

    # write header into CSV
    headerdict = {}
    for i in headers:
        headerdict[i] = i
    yield writer.writerow(headerdict)

    # write data into CSV
    for scan in scans.scan():
        flatscan = scan.to_dict()
        flatten_dict(flatscan, max_depth)
        # if we have data.invalid, then remove it and make sure the rest of the fields are there
        try:
            del flatscan['data.invalid']
            for i in headers:
                if i not in flatscan:
                    flatscan[i] = ''
        except KeyError:
            pass
        yield writer.writerow(flatscan)


def retrieve_csv(request, scantype=None, date=None):
    """A view that streams a large CSV file."""
    scans = get_scans_from_ES(request=request, scantype=scantype, date=date, raw=True)

    # skip over invalid data to get the real deal
    for hit in scans:
        firsthit = hit.to_dict()
        try:
            if firsthit['data']['invalid']:
                continue
        except KeyError:
            break

    # These scans include variable field names - so just dump each top-level
    # field as a JSON string:
    if scantype == 'pshtt':
        max_depth = 4
    elif scantype == 'lighthouse':
        max_depth = 2
    else:
        max_depth = None

    flatten_dict(firsthit, max_depth)
    fieldnames = list(firsthit.keys())

    response = StreamingHttpResponse(iter_items(scans, CSVEcho(), fieldnames, max_depth), content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="scans.csv"'
    return response


# This gets all the unique values for a field
def uniquevalues(date=None, scantype=None, field=None, subfield=None):
    if date is None:
        # default to most recent date
        date = get_dates()[1]

    if scantype is None:
        raise Exception('no scantype specified')

    index = date + '-' + scantype
    things = get_list_from_fields(index, field, subfield=subfield)
    return things


class ListsViewset(viewsets.GenericViewSet):
    queryset = ''
    serializer_class = ScanSerializer

    #def get_serializer_class(self, *args, **kwargs):
    #    return None

    def dates(self, request):
        dates = get_dates()[1:]
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
