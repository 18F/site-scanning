# Site Scanning System Description

The Site Scanning program is a free service that looks for important features on federal websites. Sites with many of these features are often more successful. 

There are three (3) components to the Site Scanning system:
* The Scanning Engine runs scans on the domains and stores the results.
* Scanning Engine Plugins are single scans of different types. The scanning engine uses the plugins for its scans. Each plugin can also run on demand.
* Scan Result UI/API is a website to view and search scan results.

## About the Scans

### Digital Analytics Program (DAP) Scan

The DAP Scan loads each website using headless Chrome and tracks each outgoing request to third party services. From these, the scan looks for specific language used to report to the DAP. By noting which websites report to DAP, the scan then can know which websites have implemented DAP. It also is able to parse out any optional parameters that the website may be passing to DAP as well.

[DAP Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/DAP.md)

### Status Scan 

The Status Scan takes each target website (e.g. www.agency.gov) and appends a list of specific paths (e.g. /data). It then tries to request each combined URL (e.g. www.agency.gov/data) and notes the resulting server code.

[Status Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/status.md)

### Sitemap Scan 

The Sitemap Scan looks at each website’s robots.txt and sitemap.xml files, if present. The scan then records the final location of the sitemap, the server status code, any sitemap locations in robots.txt file, and the number of pages/URLs counted in each sitemap. 

[Sitemap Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/sitemap.md)

### Security Scan 

The Security Scan runs security tests developed by DHS to check if specific best practices are being followed on each scanned domain.

[Security Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/security.md)

### Privacy Page Scan

The Privacy Page Scan looks for the presence of a Privacy Program/Policy Page in the expected location (`x.gov/privacy`). If present, the scan then records the email addresses listed on the page and the contents of any major section headings (`h1`, `h2`, and `h3`).

[Privacy Page Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/privacy.md)

### Page Data Scan 

The Page Data Scan checks locations on each website for a variety of characteristics including:
- server response code
- final URL 
- if final URL is redirecting to a different domain
- the content length and type
- number of JSON data items (if present)
- and more 

[Page Data Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/pagedata.md)

### U.S. Web Design System (USWDS) Scan 

The USWDS scan checks each domain for the use of U.S. Web Design System (USWDS) code and version.

[USWDS Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/uswds.md)

### Third Party Services Scan 

The Third Party Services Scan checks and logs any outside (third party) websites and services that are called from a specific .gov webpage.

[Third Party Services Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/third-party.md)

### Lighthouse Scan

The Lighthouse Scan is a set of scans selected from the open source Google Lighthouse project. The scans look for and catalog accessibility, performance and search engine optimization (SEO), and mobile-friendliness metrics for each page scanned.

[Lighthouse Scan documentation page](https://github.com/18F/site-scanning-documentation/blob/main/scans/live/lighthouse.md)
