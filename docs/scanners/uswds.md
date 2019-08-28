# U.S. Web Design System (USWDS) Scanner

## Summary
A [scan](https://site-scanning.app.cloud.gov/searchUSWDS/) to check each domain for the presence or absence of a USWDS component (i.e. font, style sheet) and the version in use of USWDS.

Specifically, the scan [searches for](https://github.com/18F/domain-scan/blob/tspencer/200scanner/scanners/uswds2.py#L36-L123): presence of `-usa` class in the style sheets, `uswds` in html text, `.usa-` in html text, `favicon-57.png` (the USWDS flag) on a website, checks for the fonts used by USWDS (current and former versions) - `Public Sans`, `Source Sans`, and `Merriweather`, searches for `uswds` or `uswds version` or `flavicon-57.png` in CSS.

* USWDS adoption
* USWDS configuration

## Details

### USWDS adoption

#### Summary
Detects whether USWDS is in use on an agency website.

#### Relevant Policy
"An executive agency that creates a website or digital service that is intended for use by the public, or conducts a redesign of an existing legacy website or digital service that is intended for use by the public, shall ensure to the greatest extent practicable that any new or redesigned website, web-based form, web-based application, or digital service has a consistent experience - _[21st Century Integrated Digital Experience Act](https://www.congress.gov/bill/115th-congress/house-bill/5759/text)_

#### Stakeholders
* OMB - Automates a part of the compliance review for [21st Century Integrated Digital Experience Act](https://www.congress.gov/bill/115th-congress/house-bill/5759/text)

#### Sample Data File

TBA

### USWDS configuration

#### Summary
Detects what version of USWDS is in use on a government website.

#### Relevant Policy
"An executive agency that creates a website or digital service that is intended for use by the public, or conducts a redesign of an existing legacy website or digital service that is intended for use by the public, shall ensure to the greatest extent practicable that any new or redesigned website, web-based form, web-based application, or digital service has a consistent experience - _[21st Century Integrated Digital Experience Act](https://www.congress.gov/bill/115th-congress/house-bill/5759/text)_

#### Stakeholders
* OMB - Automates a part of the compliance review for [21st Century Integrated Digital Experience Act](https://www.congress.gov/bill/115th-congress/house-bill/5759/text)

#### Sample Data File

TBA

#### Other Notes
* [Human curated list of USWDS sites](https://designsystem.digital.gov/getting-started/showcase/all/)



#### Version Tracking


##### v 0.3

* Added organization field
* Implemented [2nd pass at scoring rubric](https://github.com/18F/domain-scan/pull/315)

##### v 0.2

* Fixed bug that was wrongly associating 404 and 500 server codes with 200
* Added domaintype and agency 
* Refined the scoring model

##### v 0.1

* The initial rough MVP that we threw together to get started.




