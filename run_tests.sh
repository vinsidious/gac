#!/bin/bash
# Run tests with coverage properly configured
coverage run --source=gac -m pytest "$@"
coverage report --show-missing
