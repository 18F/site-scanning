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
    path('sitemap/json/', views.sitemapjson, name='sitemapjson'),
    path('sitemap/csv/', views.sitemapcsv, name='sitemapcsv'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('about/', views.about, name='about'),
    path('scans/', views.scans, name='scans-ui'),
    path('downloads/', views.downloads, name='downloads'),
    path('usecases/', views.usecases, name='usecases'),
    path('getstarted/', views.getstarted, name='getstarted'),
    path('helpus/', views.helpus, name='helpus'),
    path('contact/', views.contact, name='contact'),
    path('presentationlayers/', views.presentationlayers, name='presentationlayers'),

    path('', views.index, name='index'),
]
