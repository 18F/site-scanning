# 10x site scanning

## Background
### What is site scanning?
Site scanning is the act of making simple queries to a defined list of government websites, to evaluate compliance with basic government standards and practices. They run automatically, and, with the use of serverless cloud infrastructure, cost about two dollars per daily scan.

### What is 10x?
[10x](https://10x.gsa.gov/) is an incremental investment fund inside the United States federal government. We fund internal projects that can scale across the federal government or significantly improve how our government builds technology for the public good.

### Past scanning efforts
From 2011 to 2015, Ben Balter, a staffer within the Office of the Chief Information Officer at the Executive Office of the President and later a Presidential Innovation Fellow, performed an [analysis of federal.gov domains](https://ben.balter.com/2015/05/11/third-analysis-of-federal-executive-dotgovs/).  

Later in 2015, Jon Tindle (OGP), Eric Mill (TTS), and Gray Brooks (TTS) built https://pulse.cio.gov/ and the [two open-source site scanners](https://github.com/18F/domain-scan) that gather the data for that website: the use of [Hypertext Transfer Protocol Secure (HTTPS)](https://https.cio.gov/) and participation in the government’s [Digital Analytics Program (DAP)](https://analytics.usa.gov/).  Between 2016-2017, three other scanners were prototyped by Eric Mill, but are not currently deployed: participation in the [U.S. Web Design System](https://github.com/18F/domain-scan/commit/4458978d3871909c047319aba1102f32e6b51349), [Accessibility](https://github.com/18F/domain-scan/blob/master/scanners/a11y.py), and the use of [third-party services](https://github.com/18F/domain-scan/blob/master/scanners/third_parties.js). 

In 2016, OGP built https://digitaldashboard.gov/, which incorporates results from the Pulse HTTPS and DAP scans, as well as accessibility, mobile-responsiveness, IPv6, and Domain Name System Security Extensions (DNSSEC). Results are available to Federal employees behind a secure login. 

Between 2015 - 2017, DHS builts scans for [HTTPS](https://github.com/18F/domain-scan/blob/master/scanners/pshtt.py) and [Trusted Email](https://github.com/18F/domain-scan/blob/master/scanners/trustymail.py) to help assess whether agencies were in compliance with [Binding Operational Directives](https://cyber.dhs.gov/directives/). From these scans, DHS generates weekly “cyber hygiene reports” and sends these PDFs to agencies. 

## Overview
### Vision
TTS offers a low-cost, automated scanning solution to determine which government websites are following best practices. The results are published as simple, open data files, allowing TTS to measure TTS product performance, and agencies to customize reporting and take action to improve outcomes for the public. 

The prototype will return data that the stakeholder(s) identify as useful, and will be built and documented to make it extensible and replicable.

### Values
- Open
- Automated
- Inexpensive
- Fast

### Problem statement
The current scanning infrastructure is not actively maintained, and some prototype scanners are sitting in a dev environment, un-deployed. There is no long-term solution for storing results (cloud.gov sandbox), and site scanning not architected to be either replicable (for interested parties to stand up their own copy of site scans) or extensible (for new, custom scans to be added to the suite). 

### Prototypes
We will start with two "200 scanners": Data & APIs. 

- **Data** - This scan will return binary data on [agency].gov/data.json pages. Using this scan, we can incorporate these open data results onto [Data.gov](https://www.data.gov/) for cost savings, transparency, opportunities for small businesses, research and scientific discoveries, and improved public services. This scan can also help agencies comply with [OPEN Data Act](https://www.congress.gov/bill/115th-congress/house-bill/4174/text), [Executive Order](https://obamawhitehouse.archives.gov/the-press-office/2013/05/09/executive-order-making-open-and-machine-readable-new-default-government-), and [White House Memo](https://obamawhitehouse.archives.gov/sites/default/files/omb/memoranda/2013/m-13-13.pdf).
- **APIs**- This scan will return binary data on [agency].gov/developer pages. Using this scan, we can incorporate these open API results onto [API.data.gov](https://api.data.gov/) for cost savings and improved public services. This scan can also help agencies comply with White House Memos [M-13-13](https://obamawhitehouse.archives.gov/sites/default/files/omb/memoranda/2013/m-13-13.pdf) and [M-17-06](https://www.whitehouse.gov/sites/whitehouse.gov/files/omb/memoranda/2017/m-17-06.pdf).

### Scope of work
#### In scope
- Rearchitecting existing code to make future scanners easier to deploy, more stable, and/or more accurate
- Securing a place to house prototypes
- Developing a repeatable process to make future efforts easier
#### Out of scope
- Expanding the official .gov domain list (i.e. city, state, subdomains, etc.)
- Data visualization
- Long-term product sustainability (i.e. ownership, funding, etc.)

## Goals

| Rank          | Priority      | Goal          | Measure       |
| ------------- | ------------- |-------------  | ------------- |
| 1 | 1  | Data prototype returns data stakeholder(s) find useful and can take action on  | 1. Data - Discover data to incorporate on data.gov; show agency compliance with OPEN Data law; 2. APIs - Discover APIs to incorporate on API.data.gov; show agency compliance with White House Memos  |
| 2  | 2  | Prototype is built and documented to make it extensible and replicable  | Individual can either stand-up their own copy or add their own scan  |
| 3  | 2  | Path to scale prototype (if successful) is in place  | Recommendations for 10x phase III funding; recommendations for future scans; lessons learned; long-term data storage recommendations|


## Contact Us

If you have any questions or want to get in touch, feel free to [file an issue](https://github.com/18F/site-scanning/issues) or email us at site-scanning@gsa.gov.  
