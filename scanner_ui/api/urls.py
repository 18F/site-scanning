from django.urls import path
from .views import ListDomainsView
from .views import ListScansView

urlpatterns = [
    path('domains/', ListDomainsView.as_view(), name="domain-list"),
    path('scans/', ListScansView.as_view(), name="scan-list")
]

