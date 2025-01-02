#!/usr/bin/env bash

# Make sure we are in the virtual env
source .venv/bin/activate

# Build the package to dist/
python -m build

# Publish the package to PyPI
twine upload -r pypi dist/*
