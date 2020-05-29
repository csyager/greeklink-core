from django.db import models
from django.forms import ModelForm
from django.utils import timezone
from django.conf import settings
from django.db.models import Q


from django.contrib.auth.models import User, Group, Permission

# Stores site settings in a single model
class SiteSettings(models.Model):
    class Meta:
        verbose_name_plural = "Site Settings"
    site_title = models.CharField(max_length=100, default="test")
    primary_color_theme = models.CharField(max_length=7, default="#209CEE")
    calendar_embed = models.URLField(blank=True)
    verification_key = models.CharField(max_length=50, default="9999")
    organization_name = models.CharField(max_length=50, default="test")


# dummy model for supporting permissions
class PermissionsSupport(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('add_calendar', 'Add calendar'),
            ('delete_calendar', 'Remove calendar')
        )
#----------------------------------------------------------------------- block for resource file
class ResourceFileQuerySet(models.QuerySet):
    def search(self, query=None):
        qs = self
        if query is not None:
            or_lookup = (Q(name__icontains=query) |
                         Q(description__icontains=query) |
                         Q(file__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct() 
        return qs

class ResourceFileManager(models.Manager):
    def get_queryset(self):
        return ResourceFileQuerySet(self.model, using=self.db)

    def search(self, query=None):
        return self.get_queryset().search(query=query)

class ResourceFile(models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to="resource_files")
    description = models.CharField(max_length=280)
    extension = models.CharField(max_length=4, default="")

    objects = ResourceFileManager()

    def __str__(self):
        return self.name

#----------------------------------------------------------------------------

class OrgEvent(models.Model):
    name = models.CharField(max_length=50, default="test")
    date = models.DateField(default='2000-01-01')

    class Meta:
        abstract = True
        ordering = ['date']


#------------------------------------------------------------------ block for social event
class SocialEventQuerySet(models.QuerySet):
    def search(self, query=None):
        qs = self
        if query is not None:
            or_lookup = (Q(name__icontains=query) |
                         Q(location__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct() 
        return qs

class SocialEventManager(models.Manager):
    def get_queryset(self):
        return SocialEventQuerySet(self.model, using=self.db)

    def search(self, query=None):
        return self.get_queryset().search(query=query)


class SocialEvent(OrgEvent):
    time = models.TimeField(default='12:00')
    location = models.CharField(max_length=100, default="")
    list_limit = models.IntegerField(default=-1)
    party_mode = models.BooleanField(default=False)
    
    objects = SocialEventManager()

    def __str__(self):
        return self.name

#------------------------------------------------------------------------ block for resource link

class Attendee(models.Model):
    name = models.CharField(max_length=50)
    user = models.CharField(max_length=100)
    attended = models.BooleanField(default=False)
    event = models.ForeignKey(SocialEvent, on_delete=models.CASCADE, related_name='list')
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'event')

class ResourceLinkQuerySet(models.QuerySet):
    def search(self, query=None):
        qs = self
        if query is not None:
            or_lookup = (Q(name__icontains=query) |
                         Q(description__icontains=query) |
                         Q(url__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct() 
        return qs

class ResourceLinkManager(models.Manager):
    def get_queryset(self):
        return ResourceLinkQuerySet(self.model, using=self.db)

    def search(self, query=None):
        return self.get_queryset().search(query=query)

class ResourceLink(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=280)
    url = models.URLField(blank=False)

    objects = ResourceLinkManager()

#----------------------------------------------------------------------

class Activity(models.Model):
    action = models.CharField(max_length=100, default="test")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    target = models.URLField(default="#")
    date = models.DateTimeField(auto_now_add=True, blank=True)

#--------------------------------------------------------------------------- block for annoucement

class AnnoucementQuerySet(models.QuerySet):
    def search(self, query=None):
        qs = self
        if query is not None:
            or_lookup = (Q(title__icontains=query) |
                         Q(body__icontains=query) |
                         Q(target__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct() 
        return qs

class AnnouncementManager(models.Manager):
    def get_queryset(self):
        return AnnoucementQuerySet(self.model, using=self.db)

    def search(self, query=None):
        return self.get_queryset().search(query=query)

class Announcement(models.Model):
    title = models.CharField(max_length=100, default="test")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    target = models.URLField(default="#")
    date = models.DateTimeField(auto_now_add=True, blank=True)
    body = models.CharField(max_length=500, default="test")

    objects = AnnouncementManager()

#------------------------------------------------------------------------------