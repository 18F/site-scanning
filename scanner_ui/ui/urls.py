from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
import os

urlpatterns = [
	path('search/', views.search, name='search'),
	path('search200/', views.search200, name='search200'),
    path('', views.index, name='index'),
]
