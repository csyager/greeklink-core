from django.db import models
from django.forms import ModelForm
from django.utils import timezone
from django.conf import settings


from django.contrib.auth.models import User

# Stores site settings in a single model
class SiteSettings(models.Model):
    class Meta:
        verbose_name_plural = "Site Settings"
    site_title = models.CharField(max_length=100, default="test")
    primary_color_theme = models.CharField(max_length=7, default="#209CEE")
    calendar_embed = models.URLField(blank=True)
    verification_key = models.CharField(max_length=50, default="9999")
    organization_name = models.CharField(max_length=50, default="test")


class ResourceFile(models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to="resource_files")
    description = models.CharField(max_length=280)
    extension = models.CharField(max_length=4, default="")

    def __str__(self):
        return self.name


class OrgEvent(models.Model):
    name = models.CharField(max_length=50, default="test")
    date = models.DateField(default='2000-01-01')

    class Meta:
        abstract = True


class Attendee(models.Model):
    name = models.CharField(max_length=50, unique=True)
    user = models.CharField(max_length=100)
    attended = models.BooleanField(default=False)
    class Meta:
        ordering = ['name']


class SocialEvent(OrgEvent):
    time = models.TimeField(default='12:00')
    location = models.CharField(max_length=100, default="")
    list = models.ManyToManyField(Attendee, blank=True)

    def __str__(self):
        return self.name


class ResourceLink(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=280)
    url = models.URLField(blank=False)


class Activity(models.Model):
    action = models.CharField(max_length=100, default="test")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    target = models.URLField(default="#")
    date = models.DateTimeField(auto_now_add=True, blank=True)


class Announcement(models.Model):
    title = models.CharField(max_length=100, default="test")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    target = models.URLField(default="#")
    date = models.DateTimeField(auto_now_add=True, blank=True)
    body = models.CharField(max_length=500, default="test")