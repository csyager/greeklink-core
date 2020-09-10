import os
from urllib.parse import urljoin

from django.conf import settings
from django.utils.encoding import filepath_to_uri
from django.db import connection

from tenant_schemas.storage import TenantFileSystemStorage, TenantStorageMixin
from storages.backends.s3boto3 import S3Boto3Storage

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

class S3TenantStorage(TenantStorageMixin, S3Boto3Storage):
    """
    A class that implements Tenant-Schema's storage system combined with the S3 backend.
    """
        