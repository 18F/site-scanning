from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
import os

urlpatterns = [
	path('search/', views.search, name='search'),
    path('', views.index, name='index'),
]
