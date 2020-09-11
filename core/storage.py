import os
from urllib.parse import urljoin

from django.conf import settings
from django.utils.encoding import filepath_to_uri
from django.db import connection

from tenant_schemas.storage import TenantFileSystemStorage, TenantStorageMixin
from storages.backends.s3boto3 import S3Boto3Storage

# This safe_join is specific for S3. Do not use the normal one
from storages.utils import safe_join

class TestEnvironmentSystemStorage(TenantFileSystemStorage):
    def url(self, name):
        if settings.DEBUG:
            if self.base_url is None:
                raise ValueError("This file is not accessible via a URL.")
            url = filepath_to_uri(name)
            if url is not None:
                url = url.lstrip('/')
            print (urljoin(self.base_url, os.path.join(connection.tenant.domain_url, url)))
            return urljoin(self.base_url, os.path.join(connection.tenant.domain_url, url))
        else:
            return super().url(name)

class S3TenantStorage(S3Boto3Storage):
    """
    A class that implements a tenant aware storage system by extending the S3 backend.
    """

    """
    Normally, the location attribute of a Django Storage object is a cached property,
    and thus is not updated when the schema is changed. This function overrides the location to be
    a normal property, and sets it to the tenant domain to ensure everything is separated for each tenant.
    """
    @property
    def location(self):
        _location = connection.tenant.domain_url
        return _location
        