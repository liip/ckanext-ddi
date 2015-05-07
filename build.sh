#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check PEP-8 code style and McCabe complexity
flake8 --show-pep8 --show-source ckanext

# run tests
# nosetests --verbose
