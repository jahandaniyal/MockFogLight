#!/usr/bin/env python
import sys
import json
import yaml

with open('mapping.yml', 'w') as outfile:
    print(yaml.dump(yaml.load(json.dumps(json.loads(open("mapping.json").read()))), outfile, default_flow_style=False))
