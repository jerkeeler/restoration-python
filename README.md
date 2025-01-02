# Restoration

# **UNDER ACTIVE DEVELOPMENT** - This project is currently under active development and is not yet ready for use.

[![PyPI version](https://badge.fury.io/py/restoration.svg)](https://badge.fury.io/py/restoration)

Restore [Age of Mythology](https://www.ageofempires.com/games/aom/age-of-mythology-retold/) rec files into a human readable format (and other utilities).

## Development setup

Clone the respository, create a new virtual environment, install the package and its dependencies:

```bash
# Install the package and its dev dependencies
pip install -e .[dev]

# Setup pre-commit hooks
pre-commit install
```

## Publishing

```bash
# Install the build and twine packages
pip install build twine

# Setup .pypirc file with correct tokens
# Run the publish script to publish to pypi
./bin/publish.sh
```
