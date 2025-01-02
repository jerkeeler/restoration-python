#!/usr/bin/env bash

# Run isort and capture the result
isort --check restoration/
isort_status=$?

# Run black and capture the result
black --check restoration/
black_status=$?

# Run mypy and capture the result
mypy restoration/
mypy_status=$?

# Check if any of the linters failed
if [ $isort_status -ne 0 ] || [ $black_status -ne 0 ] || [ $mypy_status -ne 0 ]; then
    echo "Linting failed."
    exit 1
else
    echo "All linters passed."
    exit 0
fi
