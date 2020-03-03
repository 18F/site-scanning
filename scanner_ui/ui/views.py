from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
import os
import logging
import json
import csv
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from django.urls import reverse
from .viewfunctions import getdates, getquery, periodize, mixpagedatain, getListFromFields, deperiodize, popupbuilder, setdisplaytypetitle


# Create your views here.

def about(request):
    # This is just to show how to get data from python into the page.
    # You could just edit the template directly to add this static text
    # too.
    info = 'Hello world!'

    context = {
        'info': info,
    }
    return render(request, "about.html", context=context)


def scans(request):
    return render(request, "scans.html")


def downloads(request):
    return render(request, "downloads.html")


def aboutUSWDSscan(request):
    return render(request, "about-USWDS-scanner.html")


def about200scanner(request):
    return render(request, "about-200-scanner.html")


def usecases(request):
    return render(request, "use-cases.html")


def helpus(request):
    return render(request, "help-us.html")


def contact(request):
    return render(request, "contact.html")


def getstarted(request):
    return render(request, "get-started.html")


def presentationlayers(request):
    return render(request, "presentation-layers.html")


def index(request):
    dates = getdates()
    latestindex = dates[1] + '-*'
    es = Elasticsearch([os.environ['ESURL']])

    allscanscount = Search(using=es, index=latestindex).query().count()

    scantypecount = len(es.indices.get_alias(latestindex))

    s = Search(using=es, index=latestindex).query().source(['domain'])
    domainmap = {}
    for i in s.scan():
        domainmap[i.domain] = 1
    domaincount = len(domainmap)

    context = {
        'num_domains': domaincount,
        'num_scantypes': scantypecount,
        'num_scans': allscanscount,
    }
    return render(request, "index.html", context=context)


def search200json(request):
    my200page = request.GET.get('200page')
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    mimetype = request.GET.get('mimetype')
    org = request.GET.get('org')
    present = request.GET.get('present')
    displaytype = request.GET.get('displaytype')
    domainsearch = request.GET.get('domainsearch')

    if my200page is None:
        my200page = 'All Scans'

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-200scanner'

    statuscodelocation = None
    if my200page != 'All Scans':
        statuscodelocation = 'data.' + deperiodize(my200page)

    if present is None:
        present = "Present"

    # do the actual query here.
    s = getquery(index, present=present, indexbase=indexbase, page=my200page, agency=agency, domaintype=domaintype, org=org, mimetype=mimetype, statuscodelocation=statuscodelocation, domainsearch=domainsearch)

    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="200scan.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
        scan = i.to_dict()
        scandata = scan['data']

        # keys cannot have . in them, so do this to make it look proper
        del scan['data']
        scan['data'] = {}
        for k, v in scandata.items():
            scan['data'][periodize(k)] = v

        # mix in pagedata scan if we can
        if my200page != 'All Scans':
            scan = mixpagedatain(scan, indexbase)
            extradata = scan['extradata']

            # keys cannot have . in them, so do this to make it look proper
            del scan['extradata']
            scan['extradata'] = {}
            for k, v in extradata.items():
                scan['extradata'][periodize(k)] = v

        # mix in extra data if needed
        if displaytype == 'dap':
            scan = mixpagedatain(scan, indexbase, 'dap')
        if displaytype == 'third_parties':
            scan = mixpagedatain(scan, indexbase, 'third_parties')

        response.write(json.dumps(scan))
        if count > 1:
            response.write(',')
        count = count - 1
    response.write(']')

    return response


def search200csv(request):
    my200page = request.GET.get('200page')
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    mimetype = request.GET.get('mimetype')
    org = request.GET.get('org')
    present = request.GET.get('present')
    displaytype = request.GET.get('displaytype')
    domainsearch = request.GET.get('domainsearch')

    if my200page is None:
        my200page = 'All Scans'

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-200scanner'

    statuscodelocation = None
    if my200page != 'All Scans':
        statuscodelocation = 'data.' + deperiodize(my200page)

    if present is None:
        present = "Present"

    # do the actual query here.
    s = getquery(index, present=present, indexbase=indexbase, page=my200page, agency=agency, domaintype=domaintype, org=org, mimetype=mimetype, statuscodelocation=statuscodelocation, domainsearch=domainsearch)

    # pull the scan data fields out into the top level to make it look better
    # Get the fields from the mapping.
    es = Elasticsearch([os.environ['ESURL']])
    m = es.indices.get_mapping(index)

    # Searches pull data in from other scans, so add fields in from their mapping
    if displaytype == 'dap':
        extraindex = indexbase + '-dap'
    elif displaytype == 'third_parties':
        extraindex = indexbase + '-third_parties'
    else:
        extraindex = indexbase + '-pagedata'
    extram = es.indices.get_mapping(extraindex)

    fieldnames = list(m[index]['mappings']['scan']['properties'].keys())
    fieldnames.remove('data')
    for i in m[index]['mappings']['scan']['properties']['data']['properties'].keys():
        fieldnames.append(periodize(i))

    for k, v in extram[extraindex]['mappings']['scan']['properties']['data']['properties'].items():
        try:
            for field in v.keys():
                if displaytype == 'dap' or displaytype == 'third_parties':
                    fieldnames.append(k)
                else:
                    # This is data from the pagedata scan
                    fieldnames.append(periodize(k) + ' ' + field)
        except Exception:
            fieldnames.append(k)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="200scan.csv"'
    writer = csv.DictWriter(response, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for i in s.scan():
        # prepopulate all the fields so that if we are missing any, we don't throw an exception.
        scan = {}
        for f in fieldnames:
            scan[periodize(f)] = ''
        realscan = i.to_dict()
        scan.update(realscan)

        # mix in extradata
        if displaytype == 'dap':
            scan = mixpagedatain(scan, indexbase, indextype='dap')
        elif displaytype == 'third_parties':
            scan = mixpagedatain(scan, indexbase, indextype='third_parties')
        else:
            if my200page != 'All Scans':
                scan = mixpagedatain(scan, indexbase)

        # pull the scan data out into the top level to make it look better
        scandata = scan['data']
        del scan['data']
        for k, v in scandata.items():
            scan[periodize(k)] = v

        # pull the extradata out into the top level to make it look better
        if 'extradata' in scan:
            extradata = scan['extradata']
            del scan['extradata']
            for k, v in extradata.items():
                if displaytype == 'dap' or displaytype == 'third_parties':
                    scan[k] = v
                else:
                    for field, value in v.items():
                        scan[periodize(k) + ' ' + field] = value

        writer.writerow(scan)

    return response


def search200(request, displaytype=None):
    date = request.GET.get('date')
    my200page = request.GET.get('200page')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    org = request.GET.get('org')
    mimetype = request.GET.get('mimetype')
    present = request.GET.get('present')
    domainsearch = request.GET.get('domainsearch')
    hitsperpage = request.GET.get('hitsperpage')
    page_no = request.GET.get('page')

    dates = getdates()
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    if displaytype == 'dap':
        index = indexbase + '-dap'
    else:
        index = indexbase + '-200scanner'

    # search in ES for 200 pages we can select
    es = Elasticsearch([os.environ['ESURL']])
    if my200page is None:
        my200page = 'All Scans'
    s = Search(using=es, index=index).query().params(terminate_after=1)
    pagemap = {}
    try:
        for i in s.scan():
            for z in i.data.to_dict().keys():
                pagemap[periodize(z)] = 1
        my200pages = list(pagemap.keys())
    except Exception:
        my200pages = []
    my200pages.insert(0, 'All Scans')

    # get the agencies/domaintypes/orgs
    agencies = getListFromFields(index, 'agency')
    agencies.insert(0, 'All Agencies')
    domaintypes = getListFromFields(index, 'domaintype')
    domaintypes.insert(0, 'All Branches')
    orgs = getListFromFields(index, 'organization')
    orgs.insert(0, 'All Organizations')

    if agency is None:
        agency = 'All Agencies'

    if domaintype is None:
        domaintype = 'All Branches'

    if org is None:
        org = 'All Organizations'

    # Find list of mime types from the pagedata index
    mimetypes = getListFromFields(indexbase + '-pagedata', 'data', subfield='content_type')
    mimetypes.insert(0, 'all content_types')
    if mimetype is None:
        mimetype = 'all content_types'

    # find whether we want to do present/notpresent/all
    if present is None:
        if displaytype == 'dap' or displaytype == 'third_parties':
            present = "All"
        else:
            present = "Present"
    presentlist = [
        "Present",
        "Not Present",
        "All"
    ]

    statuscodelocation = None
    if my200page != 'All Scans':
        statuscodelocation = 'data.' + deperiodize(my200page)

    # do the actual query here.
    s = getquery(index, present=present, indexbase=indexbase, page=my200page, agency=agency, domaintype=domaintype, org=org, mimetype=mimetype, statuscodelocation=statuscodelocation, domainsearch=domainsearch, displaytype=displaytype)

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    if hitsperpage is None:
        hitsperpage = hitsperpagelist[1]
    if page_no is None:
        page_no = 1
    paginator = Paginator(s, int(hitsperpage))
    try:
        page = paginator.page(page_no)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    results = page.object_list.execute()

    # mix in the appropriate scan into the page we are displaying.
    pagedomainlist = []
    # get list of domains to search for in the proper index
    for i in results:
        pagedomainlist.insert(0, i.domain)

    # search the proper index
    if displaytype is None:
        displaytypeindex = indexbase + '-pagedata'
    else:
        displaytypeindex = indexbase + '-' + displaytype
    if es.indices.exists(index=displaytypeindex):
        s = Search(using=es, index=displaytypeindex).filter('terms', domain=pagedomainlist)
    else:
        s = Search(using=es, index=indexbase + '-pagedata').filter('terms', domain=pagedomainlist)

    # get data from the other index
    extradata = {}
    try:
        for i in s.scan():
            extradata[i.domain] = i.data.to_dict()
    except Exception:
        logging.error('could not find other index to create the extradata')

    # create columns for us to render in the page
    columns = []

    # create a default set of popups
    # popups are just a data structure that is iterated over to generate popups in
    # the page template.
    popups = []
    popups.append(popupbuilder('present', presentlist, selectedvalue=present))
    popups.append(popupbuilder('200page', my200pages, selectedvalue=periodize(my200page)))
    popups.append(popupbuilder('date', dates, selectedvalue=date))
    popups.append(popupbuilder('agency', agencies, selectedvalue=agency))
    popups.append(popupbuilder('domaintype', domaintypes, selectedvalue=domaintype))
    popups.append(popupbuilder('org', orgs, selectedvalue=org))
    if my200page != 'All Scans':
        popups.append(popupbuilder('mimetype', mimetypes, selectedvalue=mimetype))
    else:
        popups.append(popupbuilder('mimetype', mimetypes, selectedvalue=mimetype, disabled=True))

    # set some defaults for use while looping
    selectedpage = deperiodize(my200page)

    displaytypetitle = setdisplaytypetitle(displaytype)

    for i in results:
        # Below here are where you can set up different types of pages.
        # Just create another 'elif displaytype == "yourpagetype"' section below
        # and do what the other displaytypes do:  create a column, add your data
        # to it, store it in the results and set the columns and page title.
        #
        # You can also customize the popups using the popupbuilder.
        # See the DAP scan for an example of this.
        #
        # XXX seems like there ought to be a more clever way to do this.

        # 200-dev style display
        if displaytype == '200-developer':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in extradata and my200page != 'All Scans':
                column['Final URL'] = extradata[i.domain][selectedpage]['final_url']
                column['Content Type'] = extradata[i.domain][selectedpage]['content_type']
                column['File Size (B)'] = extradata[i.domain][selectedpage]['content_length']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['File Size (B)'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())

        # 200-codejson style display
        elif displaytype == '200-codejson':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in extradata and my200page != 'All Scans':
                column['Final URL'] = extradata[i.domain][selectedpage]['final_url']
                column['Content Type'] = extradata[i.domain][selectedpage]['content_type']
                column['json Items'] = extradata[i.domain][selectedpage]['json_items']
                column['File Size (B)'] = extradata[i.domain][selectedpage]['content_length']
                column['Code.gov Measurement Type'] = extradata[i.domain][selectedpage]['codegov_measurementtype']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['json Items'] = ''
                column['File Size (B)'] = ''
                column['Code.gov Measurement Type'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())

        # 200-data.json style display
        elif displaytype == '200-data.json':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in extradata and my200page != 'All Scans':
                column['Final URL'] = extradata[i.domain][selectedpage]['final_url']
                column['Content Type'] = extradata[i.domain][selectedpage]['content_type']
                column['json Items'] = extradata[i.domain][selectedpage]['json_items']
                column['File Size (B)'] = extradata[i.domain][selectedpage]['content_length']
                column['Opendata Conformity'] = extradata[i.domain][selectedpage]['opendata_conforms_to']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['json Items'] = ''
                column['File Size (B)'] = ''
                column['Opendata Conformity'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())

        # 200-robotstxt style display
        elif displaytype == '200-robotstxt':
            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            if my200page == 'All Scans':
                column['Target URL'] = 'https://' + i.domain
                column['Status'] = ''
                column['Response Code'] = ''
            else:
                column['Target URL'] = 'https://' + i.domain + my200page
                if i.data[selectedpage] != '200':
                    column['Status'] = 'Not Present'
                else:
                    column['Status'] = 'Present'
                column['Response Code'] = i.data[selectedpage]
            if i.domain in extradata and my200page != 'All Scans':
                column['Final URL'] = extradata[i.domain][selectedpage]['final_url']
                column['Content Type'] = extradata[i.domain][selectedpage]['content_type']
                column['File Size (B)'] = extradata[i.domain][selectedpage]['content_length']
            else:
                column['Final URL'] = ''
                column['Content Type'] = ''
                column['File Size (B)'] = ''
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())

        # dap style display
        elif displaytype == 'dap':
            popups = []
            presentlist = [
                "DAP Present",
                "DAP Not Present",
                "All"
            ]
            popups.append(popupbuilder('present', presentlist, selectedvalue=present))
            popups.append(popupbuilder('date', dates, selectedvalue=date))
            popups.append(popupbuilder('agency', agencies, selectedvalue=agency))
            popups.append(popupbuilder('domaintype', domaintypes, selectedvalue=domaintype))
            popups.append(popupbuilder('org', orgs, selectedvalue=org))

            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            try:
                if extradata[i.domain]['dap_detected']:
                    column['DAP Detected'] = "True"
                else:
                    column['DAP Detected'] = "False"
                column['DAP Parameters'] = extradata[i.domain]['dap_parameters']
            except Exception:
                column['DAP Detected'] = "False"
                column['DAP Parameters'] = ""
            detailpath = reverse('domains-detail', kwargs={'domain': i.domain})
            column['Other Scan Results'] = request.build_absolute_uri(detailpath)
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())

        # third_parties style display
        elif displaytype == 'third_parties':
            popups = []
            popups.append(popupbuilder('date', dates, selectedvalue=date))
            popups.append(popupbuilder('agency', agencies, selectedvalue=agency))
            popups.append(popupbuilder('domaintype', domaintypes, selectedvalue=domaintype))
            popups.append(popupbuilder('org', orgs, selectedvalue=org))

            column = {}
            column['Domain'] = i.domain
            column['Agency'] = i.agency
            column['Organization'] = i.organization
            column['Branch'] = i.domaintype
            try:
                column['Known Services'] = ', '.join(extradata[i.domain]['known_services'])
                column['Unknown Service Domains'] = ', '.join(extradata[i.domain]['unknown_services'])
            except Exception:
                column['Known Services'] = []
                column['Unknown Service Domains'] = []
            detailpath = reverse('domains-detail', kwargs={'domain': i.domain})
            column['Other Scan Results'] = request.build_absolute_uri(detailpath)
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())

        # default to the basic 200 scans search
        else:
            column = {}
            if my200page == 'All Scans':
                column['Domain'] = 'https://' + i.domain
            else:
                column['Domain'] = 'https://' + i.domain + my200page
            column['Branch'] = i.domaintype
            column['Agency'] = i.agency
            if my200page == 'All Scans':
                column['Response Code'] = ''
            else:
                column['Response Code'] = i.data[selectedpage]
            if i.domain in extradata and my200page != 'All Scans':
                column['File Size (B)'] = extradata[i.domain][selectedpage]['content_length']
                column['Content Type'] = extradata[i.domain][selectedpage]['content_type']
                column['Final URL'] = extradata[i.domain][selectedpage]['final_url']
                column['json Items'] = extradata[i.domain][selectedpage]['json_items']
                column['Opendata Conformity'] = extradata[i.domain][selectedpage]['opendata_conforms_to']
                column['Code.gov Measurement Type'] = extradata[i.domain][selectedpage]['codegov_measurementtype']
            else:
                column['File Size (B)'] = ''
                column['Content Type'] = ''
                column['Final URL'] = ''
                column['json Items'] = ''
                column['Opendata Conformity'] = ''
                column['Code.gov Measurement Type'] = ''
            detailpath = reverse('domains-detail', kwargs={'domain': i.domain})
            column['Other Scan Results'] = request.build_absolute_uri(detailpath)
            # store the column in the result, also populate the columns now, since
            # the results seem to be a type of dictionary that doesn't respond to .keys()
            columns = list(column.keys())
            i['column'] = list(column.values())
            if displaytype is None or displaytype == 'None':
                displaytypetitle = '200 Scans Search'
            else:
                # We should never hit this, but if we do, we will still display a page, and the displaytype will help us debug.
                displaytypetitle = '200 Scans Search: ' + displaytype

    context = {
        'search_results': results.hits,
        'selected_date': date,
        'selected_200page': periodize(my200page),
        'page_obj': page,
        'selected_agency': agency,
        'selected_domaintype': domaintype,
        'selected_present': present,
        'selected_mimetype': mimetype,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'selected_org': org,
        'columns': columns,
        'displaytype': displaytype,
        'displaytypetitle': displaytypetitle,
        'selected_domainsearch': domainsearch,
        'popups': popups,
    }

    return render(request, "search200.html", context=context)


def searchUSWDSjson(request):
    date = request.GET.get('date')
    query = request.GET.get('q')
    version = request.GET.get('version')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    sort = request.GET.get('sort')

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-uswds2'

    sortstring = 'domain'
    if sort == 'Score':
        sortstring = '-data.total_score'

    s = getquery(index, totalscorequery=query, version=version, agency=agency, domaintype=domaintype, sort=sortstring)
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="USWDSscan.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
        response.write(json.dumps(i.to_dict()))
        if count > 1:
            response.write(',')
        count = count - 1
    response.write(']')

    return response


def searchUSWDScsv(request):
    date = request.GET.get('date')
    query = request.GET.get('q')
    version = request.GET.get('version')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    sort = request.GET.get('sort')

    dates = getdates()
    indexbase = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-uswds2'

    sortstring = 'domain'
    if sort == 'Score':
        sortstring = '-data.total_score'

    s = getquery(index, totalscorequery=query, version=version, agency=agency, domaintype=domaintype, sort=sortstring)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="USWDSscan.csv"'

    r = s.execute()

    # pull the scan data out into the top level to make it look better
    try:
        firsthit = r.hits[0].to_dict()
        fieldnames = list(firsthit.keys())
        fieldnames.remove('data')
        for k, v in firsthit['data'].items():
            fieldnames.append(k)

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        for i in s.scan():
            scan = i.to_dict()

            # pull the scan data out into the top level to make it look better
            scandata = scan['data']
            del scan['data']
            for k, v in scandata.items():
                scan[k] = v

            writer.writerow(scan)
    except:
        writer = csv.writer(response)
        writer.writerow(['No Data'])

    return response


def searchUSWDS(request):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-uswds2'

    # get the agencies/domaintypes
    agencies = getListFromFields(index, 'agency')
    agencies.insert(0, 'All Agencies')
    domaintypes = getListFromFields(index, 'domaintype')
    domaintypes.insert(0, 'All Branches')

    agency = request.GET.get('agency')
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    sort = request.GET.get('sort')
    if sort is None:
        sort = 'Domain'
    sortinglist = ['Domain', 'Score']

    # search in ES for versions that have been detected
    es = Elasticsearch([os.environ['ESURL']])
    s = Search(using=es, index=index).query().source(['data.uswdsversion'])
    versionmap = {}
    try:
        for i in s.scan():
            if isinstance(i.data.uswdsversion, str) and i.data.uswdsversion != '':
                versionmap[i.data.uswdsversion] = 1
        versions = list(versionmap.keys())
        versions.sort()
    except:
        versions = []
    # versions = getListFromFields(index, 'data.uswdsversion')
    versions.insert(0, 'detected versions')
    versions.insert(0, 'all versions')

    version = request.GET.get('version')
    if version is None:
        version = 'all versions'

    # the query should be a number that we are comparing to total_score
    query = request.GET.get('q')
    try:
        query = int(query)
    except:
        query = 0

    sortstring = 'domain'
    if sort == 'Score':
        sortstring = '-data.total_score'

    # do the actual query here.
    s = getquery(index, totalscorequery=query, version=version, agency=agency, domaintype=domaintype, sort=sortstring)

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
        hitsperpage = hitsperpagelist[1]
    page_no = request.GET.get('page')
    if page_no is None:
        page_no = 1
    paginator = Paginator(s, int(hitsperpage))
    try:
        page = paginator.page(page_no)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    results = page.object_list.execute()

    context = {
        'search_results': results.hits,
        'dates': dates,
        'query': query,
        'selected_date': date,
        'page_obj': page,
        'agencies': agencies,
        'selected_agency': agency,
        'domaintypes': domaintypes,
        'selected_domaintype': domaintype,
        'versions': versions,
        'selected_version': version,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'sortinglist': sortinglist,
        'selected_sort': sort,
    }

    return render(request, "searchUSWDS.html", context=context)


def privacy(request):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-privacy'

    # get the agencies/domaintypes
    agencies = getListFromFields(index, 'agency')
    agencies.insert(0, 'All Agencies')
    domaintypes = getListFromFields(index, 'domaintype')
    domaintypes.insert(0, 'All Branches')

    agency = request.GET.get('agency')
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    # find whether we want to do present/notpresent/all
    present = request.GET.get('present')
    if present is None:
        present = "Present"
    presentlist = [
        "Present",
        "Not Present",
        "All"
    ]

    # do the actual query here.
    s = getquery(index, present=present, agency=agency, domaintype=domaintype, statuscodelocation='data.status_code')

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
        hitsperpage = hitsperpagelist[1]
    page_no = request.GET.get('page')
    if page_no is None:
        page_no = 1
    paginator = Paginator(s, int(hitsperpage))
    try:
        page = paginator.page(page_no)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    results = page.object_list.execute()

    # process the search results on the page so that we can format them properly
    columns = []
    for i in results:
        column = {}
        column['Domain'] = i.domain
        column['Agency'] = i.agency
        column['Organization'] = i.organization
        column['Branch'] = i.domaintype
        column['Target URL'] = 'https://' + i.domain + '/privacy'
        if i.data['status_code'] == "200":
            column['Status'] = "Is Present"
        else:
            column['Status'] = "Not Present"
        column['Response Code'] = i.data['status_code']
        column['Final URL'] = i.data['final_url']
        column['Emails'] = ' '.join(i.data['emails'])
        column['H1 Headers'] = i.data['h1']
        column['H2 Headers'] = i.data['h2']
        column['H3 Headers'] = i.data['h3']
        # store the column in the result, also populate the columns now, since
        # the results seem to be a type of dictionary that doesn't respond to .keys()
        columns = list(column.keys())
        i['column'] = list(column.values())

    title = '/privacy Page'
    blurb = 'This page will let you view information about the various /privacy pages out there'
    context = {
        'search_results': results.hits,
        'columns': columns,
        'dates': dates,
        'selected_date': date,
        'page_obj': page,
        'agencies': agencies,
        'selected_agency': agency,
        'domaintypes': domaintypes,
        'selected_domaintype': domaintype,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'presentlist': presentlist,
        'selected_present': present,
        'title': title,
        'blurb': blurb,
        'mainurl': 'privacy',
        'jsonurl': 'privacyjson',
        'csvurl': 'privacycsv',
    }
    return render(request, "customsearchpage.html", context=context)


def privacyjson(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-privacy'
    else:
        index = date + '-privacy'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype, statuscodelocation='data.status_code')
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="PrivacyPageData.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
        response.write(json.dumps(i.to_dict()))
        if count > 1:
            response.write(',')
        count = count - 1
    response.write(']')

    return response


def privacycsv(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-privacy'
    else:
        index = date + '-privacy'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype, statuscodelocation='data.status_code')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="PrivacyPageData.csv"'

    r = s.execute()

    # pull the scan data out into the top level to make it look better
    firsthit = r.hits[0].to_dict()
    fieldnames = list(firsthit.keys())
    fieldnames.remove('data')
    for k, v in firsthit['data'].items():
        fieldnames.append(k)

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()

    for i in s.scan():
        scan = i.to_dict()

        # pull the scan data out into the top level to make it look better
        scandata = scan['data']
        del scan['data']
        for k, v in scandata.items():
            scan[k] = v

        writer.writerow(scan)

    return response


def sitemap(request):
    dates = getdates()

    date = request.GET.get('date')
    if date == 'None' or date == 'Scan Date' or date is None:
        indexbase = dates[1]
    else:
        indexbase = date
    index = indexbase + '-sitemap'

    # get the agencies/domaintypes
    agencies = getListFromFields(index, 'agency')
    agencies.insert(0, 'All Agencies')
    domaintypes = getListFromFields(index, 'domaintype')
    domaintypes.insert(0, 'All Branches')

    agency = request.GET.get('agency')
    if agency is None:
        agency = 'All Agencies'

    domaintype = request.GET.get('domaintype')
    if domaintype is None:
        domaintype = 'All Branches'

    # find whether we want to do present/notpresent/all
    present = request.GET.get('present')
    if present is None:
        present = "Present"
    presentlist = [
        "Present",
        "Not Present",
        "All"
    ]

    # do the actual query here.
    s = getquery(index, present=present, agency=agency, domaintype=domaintype, statuscodelocation='data.status_code')

    # set up pagination here
    hitsperpagelist = ['20', '50', '100', '200']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
        hitsperpage = hitsperpagelist[1]
    page_no = request.GET.get('page')
    if page_no is None:
        page_no = 1
    paginator = Paginator(s, int(hitsperpage))
    try:
        page = paginator.page(page_no)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    results = page.object_list.execute()

    # process the search results on the page so that we can format them properly
    columns = []
    for i in results:
        column = {}
        column['Domain'] = i.domain
        column['Agency'] = i.agency
        column['Organization'] = i.organization
        column['Branch'] = i.domaintype
        column['Target URL'] = 'https://' + i.domain + '/sitemap.xml'
        if i.data['status_code'] == "200":
            column['Status'] = "Is Present"
        else:
            column['Status'] = "Not Present"
        column['Response Code'] = i.data['status_code']
        column['Final URL'] = i.data['final_url']
        column['URL Count'] = i.data['url_tag_count']
        column['Locations in robots.txt'] = ' '.join(i.data['sitemap_locations_from_robotstxt'])
        # store the column in the result, also populate the columns now, since
        # the results seem to be a type of dictionary that doesn't respond to .keys()
        columns = list(column.keys())
        i['column'] = list(column.values())

    title = 'Sitemap Page'
    blurb = 'This page will let you view information about the various /sitemap.xml pages out there'
    context = {
        'search_results': results.hits,
        'columns': columns,
        'dates': dates,
        'selected_date': date,
        'page_obj': page,
        'agencies': agencies,
        'selected_agency': agency,
        'domaintypes': domaintypes,
        'selected_domaintype': domaintype,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
        'presentlist': presentlist,
        'selected_present': present,
        'title': title,
        'blurb': blurb,
        'mainurl': 'sitemap',
        'jsonurl': 'sitemapjson',
        'csvurl': 'sitemapcsv',
    }
    return render(request, "customsearchpage.html", context=context)


def sitemapjson(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-sitemap'
    else:
        index = date + '-sitemap'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype, statuscodelocation='data.status_code')
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="sitemapData.json"'

    # write out a valid json array
    response.write('[')
    count = s.count()
    for i in s.scan():
        response.write(json.dumps(i.to_dict()))
        if count > 1:
            response.write(',')
        count = count - 1
    response.write(']')

    return response


def sitemapcsv(request):
    date = request.GET.get('date')
    agency = request.GET.get('agency')
    domaintype = request.GET.get('domaintype')
    present = request.GET.get('present')

    dates = getdates()
    index = ''
    if date == 'None' or date == 'Scan Date' or date is None:
        index = dates[1] + '-sitemap'
    else:
        index = date + '-sitemap'

    s = getquery(index, present=present, agency=agency, domaintype=domaintype, statuscodelocation='data.status_code')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sitemapData.csv"'

    r = s.execute()

    # pull the scan data out into the top level to make it look better
    firsthit = r.hits[0].to_dict()
    fieldnames = list(firsthit.keys())
    fieldnames.remove('data')
    for k, v in firsthit['data'].items():
        fieldnames.append(k)

    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()

    for i in s.scan():
        scan = i.to_dict()

        # pull the scan data out into the top level to make it look better
        scandata = scan['data']
        del scan['data']
        for k, v in scandata.items():
            scan[k] = v

        writer.writerow(scan)

    return response
