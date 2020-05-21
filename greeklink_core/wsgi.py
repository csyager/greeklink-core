"""
WSGI config for greeklink_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# attempting a fix
###########################
import time
import traceback
import signal
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greeklink_core.settings')

try:
    application = get_wsgi_application()
    print("WSGI without exception")
except Exception:
    print('handling WSGI exception')
    if 'mod_wsgi' in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)

'''
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greeklink_core.settings')

application = get_wsgi_application()
'''