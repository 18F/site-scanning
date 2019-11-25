
### Past scanning efforts

From 2011 to 2015, Ben Balter, a staffer within the Office of the Chief Information Officer at the Executive Office of the President and later a Presidential Innovation Fellow, performed an [analysis of federal.gov domains](https://ben.balter.com/2015/05/11/third-analysis-of-federal-executive-dotgovs/).  

Later in 2015, Jon Tindle (OGP), Eric Mill (TTS), and Gray Brooks (TTS) built https://pulse.cio.gov/ and the [two open-source site scanners](https://github.com/18F/domain-scan) that gather the data for that website: the use of [Hypertext Transfer Protocol Secure (HTTPS)](https://https.cio.gov/) and participation in the government’s [Digital Analytics Program (DAP)](https://analytics.usa.gov/).  Between 2016-2017, three other scanners were prototyped by Eric Mill, but are not currently deployed: participation in the [U.S. Web Design System](https://github.com/18F/domain-scan/commit/4458978d3871909c047319aba1102f32e6b51349), [Accessibility](https://github.com/18F/domain-scan/blob/master/scanners/a11y.py), and the use of [third-party services](https://github.com/18F/domain-scan/blob/master/scanners/third_parties.js). 

In 2016, OGP built https://digitaldashboard.gov/, which incorporates results from the Pulse HTTPS and DAP scans, as well as accessibility, mobile-responsiveness, IPv6, and Domain Name System Security Extensions (DNSSEC). Results are available to Federal employees behind a secure login. 

Between 2015 - 2017, DHS builts scans for [HTTPS](https://github.com/18F/domain-scan/blob/master/scanners/pshtt.py) and [Trusted Email](https://github.com/18F/domain-scan/blob/master/scanners/trustymail.py) to help assess whether agencies were in compliance with [Binding Operational Directives](https://cyber.dhs.gov/directives/). From these scans, DHS generates weekly “cyber hygiene reports” and sends these PDFs to agencies. 
