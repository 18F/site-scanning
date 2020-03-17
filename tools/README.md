# Tools!

This directory contains some example tools that you can use directly, or you
can use as examples to build your own tools that query the site-scanner
API.

The only really tricky thing that the API requires you to do is use pagination
for many of the endpoints, because otherwise you run the application out
of memory.  The example scripts here have code in them to handle pagination,
and also use http sessions to speed up the process.

## newcodegovsites.py

This script looks for new sites that have `/code.json` files.  By default,
it looks back over 20 days, but if you give it an argument, it will try to
look back your specified number of days.  If it can't look back that far,
it will choose the oldest date archived to compare against.

usage: 
* `./newcodegovsites.py` to look back 20 days
* `./newcodegovsites.py 5` to look back 5 days

## newprivacypages.py

This script looks for new sites that have `/privacy` pages.  By default,
it looks back over 20 days, but if you give it an argument, it will try to
look back your specified number of days.  If it can't look back that far,
it will choose the oldest date archived to compare against.

usage: 
* `./newprivacypages.py` to look back 20 days
* `./newprivacypages.py 5` to look back 5 days

## newuswdssites.py

This script looks for new sites that have USWDS analysis numbers that are
greater than what you have specified.

usage: 
* `./newuswdssites.py` to look back 20 days for new sites with an analysis number greater than 50.
* `./newuswdssites.py 100 5` to look back 5 days for new sites with an analysis number greater than 100.
