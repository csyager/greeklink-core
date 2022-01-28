""" database models for the rush app """

from django.db import models
from core.models import User, OrgEvent
from django.urls import reverse
from django.dispatch import receiver


YEAR_CHOICES = (
    (1, 'Freshman'),
    (2, 'Sophomore'),
    (3, 'Junior'),
    (4, 'Senior')
)

# Create your models here.
class Rushee(models.Model):
    """ Represents a Rushee, or individual being considered for membership
        name -- rushee's name
        email -- email address
        year -- class in school, i.e. Freshman, Sophomore, Junior, or Senior
        major -- field of study
        hometown -- hometown, stored as string
        address -- current address, stored as string
        phone_number -- phone number, stored as string, max 10 characters
        endorsements -- Users who have endorsed this rushee
        oppositions -- Users who have opposed this rushee
        profile_picture -- picture taken at signin, stored as a file
        voting_open -- boolean value, if true votes cast for this rushee will be tallied
                       if false votes cast will not be tallied
        y -- votes cast 'yes'
        n -- votes cast 'no'
        a -- votes cast 'abstain'
        b -- votes cast 'blackball'
        blackball_list -- list of Users who cast a blackball vote
        round -- current voting round of this rushee
        cut -- if 0, rushee has not been cut (removed from consideration),
               otherwise represents which round the rushee was cut
    """

    name = models.CharField(max_length=50)
    email = models.EmailField()
    year = models.IntegerField(choices=YEAR_CHOICES, default=1)
    major = models.CharField(max_length=50)
    hometown = models.CharField(max_length=75)
    address = models.CharField(max_length=75)
    phone_number = models.CharField(max_length=10)

    in_person = models.BooleanField(default=True)
    friends_rushing = models.CharField(max_length=100, default="")

    endorsements = models.ManyToManyField(User, related_name="endorsed_rushees", blank=True)
    oppositions = models.ManyToManyField(User, related_name="opposed_rushees", blank=True)

    profile_picture = models.ImageField(upload_to='profile_pictures',
                                        default="", null=True, blank=True)

    voting_open = models.BooleanField(default=False)
    y = models.IntegerField(default=0)
    n = models.IntegerField(default=0)
    a = models.IntegerField(default=0)
    b = models.IntegerField(default=0)

    blackball_list = models.ManyToManyField(User, related_name="blackballed_rushees", blank=True)

    round = models.IntegerField(default=1)
    cut = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@receiver(models.signals.pre_delete, sender=Rushee)
def delete_s3_image(sender, instance, **kwargs):
    if instance.profile_picture:
        instance.profile_picture.delete(save=False)


class Comment(models.Model):
    """ a comment left by a User on a rushee
        name -- name of User leaving the comment
        body -- body text of the comment
        rushee -- which Rushee the comment is being left on
    """

    name = models.CharField(max_length=50)
    body = models.CharField(max_length=280)
    rushee = models.ForeignKey(Rushee, on_delete=models.CASCADE)

    def __str__(self):
        return "Comment " + str(self.pk)

class RushEvent(OrgEvent):
    """ OrgEvent (defined in core/models.py) representing a rush event
        round -- which voting round this event falls into
        attendance -- list of Rushees who attended the event
        intake_event -- boolean value, if true rushees will be presented with
                        registration form by default at signin
    """
    round = models.IntegerField(default=1)
    attendance = models.ManyToManyField(Rushee, blank=True)
    intake_event = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.name

    def get_url(self):
        return reverse('rush:event', kwargs=dict(event_id=self.pk))