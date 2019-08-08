from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
import os

urlpatterns = [
	path('search200/json/', views.search200json, name='search200json'),
	path('search200/csv/', views.search200csv, name='search200csv'),
	path('search200/', views.search200, name='search200'),
	path('searchUSWDS/json/', views.searchUSWDSjson, name='searchUSWDSjson'),
	path('searchUSWDS/csv/', views.searchUSWDScsv, name='searchUSWDScsv'),
	path('searchUSWDS/', views.searchUSWDS, name='searchUSWDS'),
	path('about/', views.about, name='about'),
    path('', views.index, name='index'),
]
