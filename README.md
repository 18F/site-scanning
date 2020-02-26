# 10x Site Scanner 

Site Scanner enables on-demand analysis of any federal domain.

This repository is for all of [Site Scanner's](https://site-scanning.app.cloud.gov/) code.

# Overview #
Site Scanner scans all domains [from this list updated monthly by GSA](https://github.com/18F/site-scanning/edit/Eleni-public-friendly/scanner_ui/ui/templates/about.html).

## Previous scanning efforts in federal government ##
- From 2011 to 2015, Ben Balter, a staffer within the Office of the Chief Information Officer at the Executive Office of the President and later a Presidential Innovation Fellow, performed an [analysis of federal.gov domains](https://ben.balter.com/2015/05/11/third-analysis-of-federal-executive-dotgovs/).   

- Later in 2015, Jon Tindle (OGP), Eric Mill (TTS), and Gray Brooks (TTS) built https://pulse.cio.gov/ and the [two open-source site scanners](https://github.com/18F/domain-scan) that gather the data for that website: the use of [Hypertext Transfer Protocol Secure (HTTPS)](https://https.cio.gov/) and participation in the government’s [Digital Analytics Program (DAP)](https://analytics.usa.gov/).  Between 2016-2017, three other scanners were prototyped by Eric Mill, but are not currently deployed: participation in the [U.S. Web Design System](https://github.com/18F/domain-scan/commit/4458978d3871909c047319aba1102f32e6b51349), [Accessibility](https://github.com/18F/domain-scan/blob/master/scanners/a11y.py), and the use of [third-party services](https://github.com/18F/domain-scan/blob/master/scanners/third_parties.js). 

- In 2016, OGP built https://digitaldashboard.gov/, which incorporates results from the Pulse HTTPS and DAP scans, as well as accessibility, mobile-responsiveness, IPv6, and Domain Name System Security Extensions (DNSSEC). Results are available to Federal employees behind a secure login. 

- Between 2015 - 2017, DHS builts scans for [HTTPS](https://github.com/18F/domain-scan/blob/master/scanners/pshtt.py) and [Trusted Email](https://github.com/18F/domain-scan/blob/master/scanners/trustymail.py) to help assess whether agencies were in compliance with [Binding Operational Directives](https://cyber.dhs.gov/directives/). From these scans, DHS generates weekly “cyber hygiene reports” and sends these PDFs to agencies. 

## Site Scanner Development History

So far, users have interacted with Site Scanner through presentation layers customized to their specific needs. The presentation layers below were launched July-November 2019. Here are their current versions:

* Data.json: v0.2 (October 2019)
* Code.json: v0.2 (October 2019)
* DAP: v0.1 (November 2019)
* /Data: v0.2
* /Developer: v0.2
* /Privacy: v0.2 (October 2019)
* Robots.txt: v0.2 (October 2019)
* Sitemaps.txt: v0.2 (October 2019)
* Third Party Services: v0.1 (November 2019)
* USWDS: v0.2 (October 2019)

## Contact Us

If you have any questions or want to get in touch, feel free to [file an issue](https://github.com/18F/site-scanning/issues) or email us at site-scanning@gsa.gov.  
