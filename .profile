#!/bin/sh
#
# This script is executed by cloud foundry
#

if [ ! -d domain-scan ] ; then
	echo installing domain-scan
	git clone https://github.com/18F/domain-scan --depth 1
fi
cd domain-scan
pip3 install -r requirements.txt
pip3 install -r requirements-scanners.txt

# install aws cli
pip3 install awscli --upgrade --user
