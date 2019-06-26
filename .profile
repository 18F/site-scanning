#!/bin/sh
#
# This script is executed by cloud foundry each time
# an instance is launched.
#


# initialize db and stuff
python3 manage.py migrate
