from django.db import models
from tenant_schemas.models import TenantMixin

# Create your models here.

class Community(models.Model):
    """ represents a community, which contains multiple Clients
        name -- string representing the name of the community
    """
    name = models.CharField(max_length=100)

class Client(TenantMixin):
    """ represents an organization with their own schema
        name -- name of the organization
        community -- name of the community containing this client (ex. UVA)
        paid_until -- end date as far as the group has paid for usage
        created_on -- date created
        auto_create_schema -- if True automatically creates a schema when new client is saved
    """
    name = models.CharField(max_length=100)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='clients', blank=True, null=True)
    paid_until = models.DateField(blank=True, null=True)
    created_on = models.DateField(auto_now_add=True)
    auto_create_schema = True
