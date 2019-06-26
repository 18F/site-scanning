#!/bin/sh
#
# This script will launch the development server on localhost
#

if [ -d venv ] ; then
	. venv/bin/activate
else
	virtualenv --python=python3 venv
	pip install -r requirements.txt
fi

DEBUG=True python manage.py runserver
