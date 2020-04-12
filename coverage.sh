#!/usr/bin/env bash

# erase existing coverage report
coverage erase
# run new coverage report
coverage run --source='.' manage.py test core
# open results in web browser
python -m webbrowser htmlcov/index.html