# Site Scanning System Description

The Site Scanning program looks for important features on federal websites. Sites that have these features are more successful. It is a free service. 

There are three (3) components to Site Scanner:
* The Scanning Engine runs scans on the domains and stores the results.
* Scanning Engine Plugins are single scans of different types. The scanning engine uses the plugins for its scans. Each plugin can also run on demand.
* Scan Result UI/API is a website to view and search scan results.



### DAP Scan

The DAP scan loads each website using headless Chrome and tracks each outgoing request to third party services.  From these, the scan looks for the specific language used to report to DAP.  By noting which websites report to DAP, the scan then can know which websites have implemented DAP.  It also is able to parse out any optional parameters that the website may be passing to DAP as well.  


### Status Scan 

The Status scan takes each target website (e.g. www.agency.gov) and appends a list of specific paths (e.g. /data).  It then tries to request each combined URL (e.g. www.agency.gov/data) and notes the resulting server code.   
