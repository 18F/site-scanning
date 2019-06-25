from django.urls import path
from .views import ListDomainsView

urlpatterns = [
    path('scans/', ListDomainsView.as_view(), name="domain-list")
]

