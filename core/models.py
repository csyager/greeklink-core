""" database models for the core application """

from django.db import models, connection
from django.db.models import Q
from django.urls import reverse

from django.contrib.auth.models import User, Group, Permission

# Stores site settings in a single model
class SiteSettings(models.Model):
    """ Settings that affect the entire site
        site_title -- the title appearing in the navigation bar
        primary_color_theme -- the color of the navbar and other objects
        calendar_embed -- link to an embedded calendar in resources page
        verification_key -- the key requested when users are creating accounts
        organization_name -- subtitle on index
        rush_signin_active -- if enabled, allows rushees to signin to events
        num_rush_rounds -- number of voting rounds in rush
    """
    class Meta:
        verbose_name_plural = "Site Settings"
    site_title = models.CharField(max_length=100, default="test")
    primary_color_theme = models.CharField(max_length=7, default="#209CEE")
    calendar_embed = models.URLField(blank=True)
    verification_key = models.CharField(max_length=50, default="9999")
    organization_name = models.CharField(max_length=50, default="test")
    rush_signin_active = models.BooleanField(default=False)
    num_rush_rounds = models.IntegerField(default=3)


# dummy model for supporting permissions
class PermissionsSupport(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('add_calendar', 'Add calendar'),
            ('delete_calendar', 'Remove calendar'),
            ('activate_rushsignin', 'Activate rushsignin')
        )
#----------------------------------------------------------------------- block for resource file

class ResourceFileQuerySet(models.QuerySet):
    """ Query set of ResourceFiles returned when using search function
        search -- returns query set based on search input
    """
    def search(self, query=None):
        """ searches for matches in name, description, or file """
        qs = self
        if query is not None:
            or_lookup = (Q(name__icontains=query) |
                         Q(description__icontains=query) |
                         Q(file__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct()
        return qs

class ResourceFileManager(models.Manager):
    """ manager for ResourceFile objects """
    def get_queryset(self):
        """ returns queryset """
        return ResourceFileQuerySet(self.model, using=self.db)

    def search(self, query=None):
        """ returns ResourceFileQuerySet.search() """
        return self.get_queryset().search(query=query)

class ResourceFile(models.Model):
    """ file stored on database for access through resources page
        name -- title of the file
        file -- corresponds to path to document
        description -- short description of the file
        extension -- file extension
    """
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to="resource_files")
    description = models.CharField(max_length=500)
    extension = models.CharField(max_length=4, default="")

    objects = ResourceFileManager()

    def __str__(self):
        return self.name

#----------------------------------------------------------------------------

class OrgEvent(models.Model):
    """ superclass for rush events and social events
        name -- name of event
        date -- date of event
        time -- time of event
        location -- location of event
    """
    name = models.CharField(max_length=50, default="test")
    date = models.DateField(default='2000-01-01')
    time = models.TimeField(default='12:00')
    location = models.CharField(max_length=100, default="")

    class Meta:
        abstract = True
        ordering = ['date']


#------------------------------------------------------------------ block for social event
class SocialEventQuerySet(models.QuerySet):
    """ QuerySet of SocialEvents returned when using search function """
    def search(self, query=None):
        """ searches for name and location matching query """
        qs = self
        if query is not None:
            or_lookup = (Q(name__icontains=query) |
                         Q(location__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct()
        return qs

class SocialEventManager(models.Manager):
    """ Manager for social event objects """
    def get_queryset(self):
        """ returns SocialEventQuerySet """
        return SocialEventQuerySet(self.model, using=self.db)

    def search(self, query=None):
        """ returns SocialEventQuerySet.search() """
        return self.get_queryset().search(query=query)


class SocialEvent(OrgEvent):
    """ OrgEvent representing a social event
        list_limit -- number of people each member is allowed to add to list
        party_mode -- while on enables list updates through ajax calls
                      and disables adding to the list
    """
    list_limit = models.IntegerField(default=-1)
    party_mode = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    objects = SocialEventManager()

    def __str__(self):
        return self.name

    def get_url(self):
        return reverse('social_event', kwargs=dict(event_id=self.pk))

#------------------------------------------------------------------------ block for resource link

class Attendee(models.Model):
    """ Social event attendee
        name -- name
        user -- User object representing member who added them to the list
        attended -- boolean, if true, already checked in to event
        event -- which event this attendee is on the list for
    """
    name = models.CharField(max_length=50)
    user = models.CharField(max_length=100)
    attended = models.BooleanField(default=False)
    event = models.ForeignKey(SocialEvent, on_delete=models.CASCADE, related_name='list')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'event')

class Roster(models.Model):
    """ List of RosterMembers representing a saved roster
        title -- title of roster
        last_updated -- datetime of last update to roster
    """
    title = models.CharField(max_length=50)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class RosterMember(models.Model):
    """ name saved to roster
        name -- name
        roster -- roster object to which this member belongs
    """
    name = models.CharField(max_length=50)
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name='members')

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'roster')

class ResourceLinkQuerySet(models.QuerySet):
    """ QuerySet for ResourceLinks used in search function """
    def search(self, query=None):
        """ searches for name, description, or url matching query """
        qs = self
        if query is not None:
            or_lookup = (Q(name__icontains=query) |
                         Q(description__icontains=query) |
                         Q(url__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct()
        return qs

class ResourceLinkManager(models.Manager):
    """ Manager for ResourceLink objects """
    def get_queryset(self):
        """ returns ResourceLinkQuerySet """
        return ResourceLinkQuerySet(self.model, using=self.db)

    def search(self, query=None):
        """ returns ResourceLinkQuerySet.search() """
        return self.get_queryset().search(query=query)

class ResourceLink(models.Model):
    """ Link to be displayed on resources page
        name -- name of link
        description -- short description of the link
        url -- URL address that the link references
    """
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    url = models.URLField(blank=False)

    objects = ResourceLinkManager()

#----------------------------------------------------------------------

class Activity(models.Model):
    """ represents user action to be recorded """
    action = models.CharField(max_length=100, default="test")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    target = models.URLField(default="#")
    date = models.DateTimeField(auto_now_add=True, blank=True)

#--------------------------------------------------------------------------- block for annoucement

class AnnoucementQuerySet(models.QuerySet):
    """ Query Set for announcements used in search function """
    def search(self, query=None):
        """ searches for title, body, or target matching query """
        qs = self
        if query is not None:
            or_lookup = (Q(title__icontains=query) |
                         Q(body__icontains=query) |
                         Q(target__icontains=query)
                        )
            qs = qs.filter(or_lookup).distinct()
        return qs

class AnnouncementManager(models.Manager):
    """ Manager for announcement objects """
    def get_queryset(self):
        """ returns AnnouncementQuerySet """
        return AnnoucementQuerySet(self.model, using=self.db)

    def search(self, query=None):
        """ returns AnnouncementQuerySet.search() """
        return self.get_queryset().search(query=query)

class Announcement(models.Model):
    """ Announcement to be displayed on the landing page for members to see
        title -- title of announcement
        user -- user posting the announcement
        target -- announcement can link to another URL, contained in this object
        date -- date announcement is posted
        body -- body text of the announcement
    """
    title = models.CharField(max_length=100, default="test")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    target = models.URLField(default="#")
    date = models.DateTimeField(auto_now_add=True, blank=True)
    body = models.CharField(max_length=500, default="test")

    objects = AnnouncementManager()

    def __str__(self):
        return self.title

    def get_url(self):
        return reverse('announcement', kwargs=dict(announcement_id=self.pk))
