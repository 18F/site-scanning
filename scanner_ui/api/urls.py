from django.urls import path
from .views import DomainsViewset
from .views import ScansViewset
from .views import ListsViewset

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
agencies = ListsViewset.as_view({
    'get': 'agencies'
})
domaintypes = ListsViewset.as_view({
    'get': 'domaintypes'
})
fieldvalues = ListsViewset.as_view({
    'get': 'fieldvalues'
})
dates = ListsViewset.as_view({
    'get': 'dates'
})

urlpatterns = [
    path('domains/', domains_list, name="domains-list"),
    path('domains/<domain>/', domains_detail, name="domains-detail"),
    path('domains/<domain>/<scantype>/', scan, name="scan"),

    path('scans/', scans_list, name="scans-list"),
    path('scans/<scantype>/', scans_detail, name="scans-detail"),
    path('scans/<scantype>/<domain>/', scan, name="scan"),

    path('lists/<scantype>/agencies/', agencies, name="agencies"),
    path('lists/<scantype>/domaintypes/', domaintypes, name="domaintypes"),
    path('lists/<scantype>/values/<field>/', fieldvalues, name="fieldvalues"),
    path('lists/<scantype>/values/<field>/<subfield>/', fieldvalues, name="subfieldvalues"),
    path('lists/dates/', dates, name="dates"),

    path('date/<date>/domains/', domains_list, name="date-domains-list"),
    path('date/<date>/domains/<domain>/', domains_detail, name="date-domains-detail"),
    path('date/<date>/domains/<domain>/<scantype>/', scan, name="date-scan"),
    path('date/<date>/scans/', scans_list, name="date-scans-list"),
    path('date/<date>/scans/<scantype>/', scans_detail, name="date-scans-detail"),
    path('date/<date>/scans/<scantype>/<domain>/', scan, name="date-scan"),
    path('date/<date>/lists/<scantype>/agencies/', agencies, name="date-agencies"),
    path('date/<date>/lists/<scantype>/domaintypes/', domaintypes, name="date-domaintypes"),
    path('date/<date>/lists/<scantype>/values/<field>/', fieldvalues, name="date-fieldvalues"),
    path('date/<date>/lists/<scantype>/values/<field>/<subfield>/', fieldvalues, name="date-subfieldvalues"),
]
