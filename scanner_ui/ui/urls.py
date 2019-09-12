from django.urls import path
from . import views

urlpatterns = [
    path('search200/json/', views.search200json, name='search200json'),
    path('search200/csv/', views.search200csv, name='search200csv'),
    path('search200/', views.search200, name='search200'),
    path('search200/<displaytype>/', views.search200, name='search200'),
    path('searchUSWDS/json/', views.searchUSWDSjson, name='searchUSWDSjson'),
    path('searchUSWDS/csv/', views.searchUSWDScsv, name='searchUSWDScsv'),
    path('searchUSWDS/', views.searchUSWDS, name='searchUSWDS'),
    path('privacy/json/', views.privacyjson, name='privacyjson'),
    path('privacy/csv/', views.privacycsv, name='privacycsv'),
    path('privacy/', views.privacy, name='privacy'),
    path('about/', views.about, name='about'),
    path('', views.index, name='index'),
]
