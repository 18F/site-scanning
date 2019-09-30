#!/usr/bin/env python3
#
# This script takes a json file as an argument and emits json where the
# keys have all periods turned into //.  Elasticsearch cannot handle
# periods in keys, so this is a tool to allow us to generate json data
# that ES can index properly.
#
import json
import sys
import re


def deperiodkeys(mydict):
    data = {}
    for k, v in mydict.items():
        data[re.sub(r'\.', '//', k)] = v
    return data


with open(sys.argv[1], 'r') as f:
    data = f.read()

jsondata = json.loads(data, object_hook=deperiodkeys)
print(json.dumps(jsondata))
