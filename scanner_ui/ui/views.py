from django.shortcuts import render
import os
import datetime
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

# Create your views here.

es = Elasticsearch([os.environ['ESURI']])

def index(request):
	yesterdayindex = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d-")
	allscanscount = Search(using=es, index=yesterdayindex).query().count()

	context = {
		'num_domains': 100,
		'num_scantypes': 2,
		'num_scans': allscanscount,
	}
	return render(request, "index.html", context=context)
