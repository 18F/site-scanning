from django.urls import path
from .views import ListScansView

urlpatterns = [
    path('scans/', ListScansView.as_view(), name="scans-all")
]

