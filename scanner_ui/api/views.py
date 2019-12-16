from rest_framework import viewsets
from rest_framework import pagination
from rest_framework.response import Response
from .serializers import ScanSerializer
import os
from scanner_ui.ui.views import getdates
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Range
import re

# Create your views here.


# get all the scans of the type and domain specified from ES.  If the type is
# None, you get all of that scantype.  If the domain is None, you
# get all domains.  If you supply a request, set the API url up
# for the scan using it.
def getScansFromES(scantype=None, domain=None, request=None):
    es = Elasticsearch([os.environ['ESURL']])
    dates = getdates()
    latestindex = dates[1] + '-*'
    indices = list(es.indices.get_alias(latestindex).keys())
    y, m, d, scantypes = zip(*(s.split("-") for s in indices))

    # if we have a valid scantype, then search that
    if scantype in scantypes:
        index = dates[1] + '-' + scantype
        s = Search(using=es, index=index)
    else:
        s = Search(using=es, index=latestindex)

    # This is to handle queries
    # arguments should be like ?domain=gsa*&data.foo=bar&numberfield=gt:50&numberfield=lt:20
    # arguments are ANDed together
    for k, v in request.GET.items():
        if re.match(r'^gt:[0-9]+', v):
            gt = v.split(':')[1]
            q = Range(**{k: {'gt': gt}})
            s = s.query(q)
        elif re.match(r'^lt:[0-9]+', v):
            lt = v.split(':')[1]
            q = Range(**{k: {'lt': lt}})
            s = s.query(q)
        else:
            s = s.query("query_string", query=v, fields=[k])

    s = s.sort('domain')

    # filter by domain if we have one
    if domain is not None:
        s = s.filter("term", domain=domain)

    # Make the api url pretty
    if request is not None:
        apiurl = request.scheme + '://' + request.get_host() + '/api/v1/scans/'

    # generate the list of scans, make the API url pretty.
    scans = []
    for i in s.scan():
        if request is not None:
            i['scan_data_url'] = apiurl + i['scantype'] + '/' + i['domain'] + '/'
        scans.append(i.to_dict())

    # # XXX
    # print(s.to_dict())

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
        if len(scan) != 1:
            raise Exception('too many or too few scans', scan)
        serializer = ScanSerializer(scan[0])
        return Response(serializer.data)
