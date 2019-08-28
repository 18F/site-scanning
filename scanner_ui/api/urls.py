from django.urls import path
from .views import DomainsViewset
from .views import ScansViewset

domains_list = DomainsViewset.as_view({
    'get': 'list'
})
domains_detail = DomainsViewset.as_view({
    'get': 'retrieve'
})
scans_list = ScansViewset.as_view({
    'get': 'list'
})
scans_detail = ScansViewset.as_view({
    'get': 'retrieve'
})
scan = ScansViewset.as_view({
    'get': 'scan'
})

urlpatterns = [
    path('domains/', domains_list, name="domains-list"),
    path('domains/<domain>/', domains_detail, name="domains-detail"),
    path('domains/<domain>/<scantype>/', scan, name="scan"),
    path('scans/', scans_list, name="scans-list"),
    path('scans/<scantype>/', scans_detail, name="scans-detail"),
    path('scans/<scantype>/<domain>/', scan, name="scan"),
]
