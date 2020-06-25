from django.db import models
from core.models import User, OrgEvent

YEAR_CHOICES = (
    (1, 'Freshman'),
    (2, 'Sophomore'),
    (3, 'Junior'),
    (4, 'Senior')
)

# Create your models here.
class Rushee(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    year = models.IntegerField(choices=YEAR_CHOICES, default=1)
    major = models.CharField(max_length=50)
    hometown = models.CharField(max_length=75)
    address = models.CharField(max_length=75)
    phone_number = models.CharField(max_length=10)
    endorsements = models.ManyToManyField(User, related_name="endorsed_rushees")
    oppositions = models.ManyToManyField(User, related_name="opposed_rushees")

    profile_picture = models.ImageField(upload_to='media/rush/profile_pictures', default="", null=True, blank=True)
    
    voting_open = models.BooleanField(default=False)
    y = models.IntegerField(default=0)
    n = models.IntegerField(default=0)
    a = models.IntegerField(default=0)
    b = models.IntegerField(default=0)

    blackball_list = models.ManyToManyField(User, related_name="blackballed_rushees")
    
    round = models.IntegerField(default=1)
    cut = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Comment(models.Model):
    name = models.CharField(max_length=50)
    body = models.CharField(max_length=280)
    rushee = models.ForeignKey(Rushee, on_delete=models.CASCADE)

    def __str__(self):
        return "Comment " + str(self.pk)

class RushEvent(OrgEvent):
    round = models.IntegerField(default=1)
    attendance = models.ManyToManyField(Rushee, blank=True)
    time = models.TimeField(default='12:00')
    location = models.CharField(max_length=100, default="")
    new_rushees_allowed = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.name

