# 10x site scanning

Site scanning is the act of making simple queries to a defined list of government websites, to evaluate compliance with basic government standards and practices. They run automatically, and, with the use of serverless cloud infrastructure, cost about two dollars per daily scan.


|  Project Links | Documentation  | Project Management  | 
|---|---|---|
|  [Homepage](https://site-scanning.app.cloud.gov/)  |  [Technical Notes](https://github.com/18F/site-scanning/tree/documentation-update/docs/technical-notes) | [Project Documents](https://github.com/18F/site-scanning/tree/documentation-update/docs/project-management)  | 
| [Use Cases For Each Scan](https://site-scanning.app.cloud.gov/use-cases/)  | [Individual Scan Details](https://github.com/18F/site-scanning/tree/documentation-update/docs/scans)  | [Project Milestones and Version History](https://github.com/18F/site-scanning/blob/documentation-update/docs/project-management/project-milestones-version-history.md) |
| [Dashboards And Other Presentation Layers](https://site-scanning.app.cloud.gov/presentation-layers/)  | [Individual Presentation Layer Details](https://github.com/18F/site-scanning/tree/documentation-update/docs/presentation-layers)  | [Past Scanning Efforts](https://github.com/18F/site-scanning/blob/documentation-update/docs/misc/history.md) |
| [API And Direct Download Links](https://site-scanning.app.cloud.gov/downloads/)  | []()  | []()  |  
| [Details Describing Each Scan](https://site-scanning.app.cloud.gov/scans/)  | []()  | []()  | 


## Overview
### Vision
TTS offers a low-cost, automated scanning solution to determine which government websites are following best practices. The results are published as simple queries and open data files, allowing TTS to measure TTS product performance, and agencies to customize reporting and take action to improve outcomes for the public. 

The prototype will return data that the stakeholder(s) identify as useful, and will be built and documented to make it extensible and replicable.

### Values
- Open
- Automated
- Inexpensive
- Fast

### Problem statement
The current scanning infrastructure is not actively maintained, and some prototype scanners are sitting in a dev environment, un-deployed. There is no long-term solution for storing results (cloud.gov sandbox), and site scanning not architected to be either replicable (for interested parties to stand up their own copy of site scans) or extensible (for new, custom scans to be added to the suite). 

### Scope of work
#### In scope
- Rearchitecting existing code to make future scanners easier to deploy, more stable, and/or more accurate
- Securing a place to house prototypes
- Developing a repeatable process to make future efforts easier
#### Out of scope
- Expanding the official .gov domain list (i.e. city, state, subdomains, etc.)
- Data visualization
- Long-term product sustainability (i.e. ownership, funding, etc.)



## Contact Us

If you have any questions or want to get in touch, feel free to [file an issue](https://github.com/18F/site-scanning/issues) or email us at site-scanning@gsa.gov.  
