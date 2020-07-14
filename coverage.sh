#!/usr/bin/env bash

# erase existing coverage report
coverage erase
# run new coverage report
coverage run manage.py test core rush
coverage html
# open results in web browser
python -m webbrowser htmlcov/index.html
open htmlcov/index.html