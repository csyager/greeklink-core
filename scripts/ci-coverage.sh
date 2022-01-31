#!/usr/bin/env bash

# erase existing coverage report
coverage erase
# run new coverage report
coverage run manage.py test
coverage xml