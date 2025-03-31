#!/usr/bin/env python3
import json
import os

# Get all environment variables
env_vars = dict(os.environ)

# Look specifically for GAC-related variables
gac_vars = {k: v for k, v in env_vars.items() if "GAC" in k or "TEST" in k}

print("GAC and TEST related environment variables:")
if gac_vars:
    for k, v in gac_vars.items():
        print(f"{k}={v}")
else:
    print("None found")

print("\nAll environment variables:")
print(json.dumps(env_vars, indent=2, sort_keys=True))
