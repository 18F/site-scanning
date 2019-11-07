This is a list of individual scans that _could_ be hosted on the Site Scanning program.  Each would likely be a standalone scan.  The list of scans that are already hosted and active is [here](https://site-scanning.app.cloud.gov/).  Feel free to suggest any ideas by [filing an issue](https://github.com/18F/site-scanning/issues) or emailing us at site-scanning@gsa.gov.      

## Office of Products and Programs (OPP) - [Data & Analytics Portfolio](https://www.gsa.gov/about-us/organization/federal-acquisition-service/technology-transformation-services/office-of-products-and-programs#DSP)

### Data.gov
* Replicate the analysis of https://labs.data.gov/dashboard/offices/qa.  

### [Digital Analytics Program (DAP)](https://digital.gov/dap/) Adoption 
* Take the full subdomain list from Pulse's https scan (roughly put, the closest we have to a complete list of all federal websites).  
* Take the full subdomain list of websites that have implemented DAP.  
* Create a crossmatch file that shows which websites have and have not implemented DAP.  
* Characteristics of the implementation (e.g. adding Agency and Sub-Agency parameters).  
* Detect CORS policy.  

### DAP Configuration
* Analyze the source code of each page that loads in order to detect the version of DAP code in use, as well as misconfigurations of the code.  

### Feedback Analytics Adoption 
* Monitor the adoption of Touchpoints.

### Use of 3rd Party Services
* Detect the loading of 3rd party services. This could detect the replication of the same tools across government for market research and opportunities to create shared services, inform the public about the use of third-party services on a website for their own privacy considerations, and alert agencies to the use of third-party services on their sites so they can monitor usage and ensure there are no "bad actors."
* May be a way to authenticate offical government social media accounts for the [U.S. Digital Registry](https://usdigitalregistry.digitalgov.gov/).

### Search.gov domain research
* Also, presence of search.gov tag

### [dcoi json files](https://www.google.com/search?q=dcoi+json&oq=dcoi+json+&aqs=chrome..69i57j33.4450j0j7&sourceid=chrome&ie=UTF-8) - [two](https://datacenters.cio.gov/reporting/strategic-plan-generator)

### [Other OMB json files](https://management.cio.gov/schema/)

### /foia 

### /cj

### FOIA XML files 

### Presence of Forms
* Analyze the source code of eage page that loads in order to detect forms and/or PRA numbers.  

## OPP - [Innovation Portfolio](https://www.gsa.gov/about-us/organization/federal-acquisition-service/technology-transformation-services/office-of-products-and-programs#IP)

### [U.S. Web Design System (USWDS)](https://designsystem.digital.gov/) Adoption
* Detect the use of USWDS on government websites.

### USWDS Configuration
* Detect the version of USWDS in use.

## OPP - [Smarter IT Delivery Portfolio](https://www.gsa.gov/about-us/organization/federal-acquisition-service/technology-transformation-services/office-of-products-and-programs#SmarterITDelivery)

### [Search.gov](https://search.gov/) Adoption
* Detect the use of Search.gov on goverment websites.


## Other Ideas


### Privacy Officers 
* more of the material from [these reports](https://www.dhs.gov/sites/default/files/publications/FY%202018%20SAOP%20FISMA%20Metrics-508c.pdf)
* Presence of PII
* Presence of forms 
* Form fields (perhaps fed from a manually generated list of URLS)


* **404 pages** - Discover `404` pages to uncover broken government websites.
* /Cj
* **Website Performance** - Monitor government website performance, possibly using [Lighthouse](https://developers.google.com/web/tools/lighthouse/).
* **Mobile Responsiveness** - Monitor government website mobile responsiveness, possibly using [Google's Mobile-Friendly Test](https://search.google.com/test/mobile-friendly).
* **CDNs** - Monitor government's content distribution networks.
* **DNS record certificate holder** - Monitor changes in agency's DNS record certificate holder, and alert agencies if there are changes, which may be a sign of malicious behavior. 
* **Social media pages** - Uncover agency's social media pages for inclusion in the [U.S. Digital Registry](https://digital.gov/services/u-s-digital-registry/).
* **HTML Metadata** - Uncover HTML metadata, which could help to populate sub-domain scanning capabilities.
* Others from https://policy.cio.gov/.
* Security scans (owasp) - https://github.com/zaproxy/zaproxy
* Mozilla Observatory scans - https://observatory.mozilla.org/analyze/www.gsa.gov
* Owasp with an eye to detecting ability to redirect (or could be done without owasp) - _[note coverage of this](https://gizmodo.com/a-year-later-u-s-government-websites-are-still-redire-1835336087)_
* For any of these scans that detect a machine readable file, copy and store in perpetuity the files themselves, so that powers that be can track trends.  
* /socialmediaTOS - Per [this](https://digital.gov/resources/federal-compatible-terms-of-service-agreements/#for-federal-agency-points-of-contact) and [this](https://www.whitehouse.gov/sites/whitehouse.gov/files/omb/memoranda/2013/m-13-10.pdf)
* more from fisma reports, as seen in [these](https://www.dhs.gov/sites/default/files/publications/FY%202018%20SAOP%20FISMA%20Metrics-508c.pdf) [questions](https://www.dhs.gov/publication/fy18-fisma-documents)
* search for what CMS sites are using - digital.gov
* Fetcher scan? - e.g. just consume the .gov database 
* Which websites use which TTS services
* others possibly could be found in [here](https://github.com/ombegov/policy-v2)

## Meta Idea
* Run scans against second level domains, subdomains, and top 500 (or) 1000 pages in DAP.  Also, consider CFO act delineations, agency delineations, what else?
