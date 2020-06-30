#!/bin/bash
# dumps data from auth database into the auth.json fixture.  Only use this if you've made changes to auth database that should be reflected in future versions of the site.
python manage.py dumpdata auth --natural-foreign --natural-primary -e auth.Permission --indent 4 > core/fixtures/auth.json
