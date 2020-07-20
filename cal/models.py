""" models for the calendar application """

from django.db import models
from core.models import OrgEvent

RECURRENCE_CHOICES = [
    ('None', 'None'),
    ('Monthly', 'Monthly'),
    ('Weekly', 'Weekly'),
    ('Daily', 'Daily')
]

class ChapterEvent(OrgEvent):
    """ OrgEvent representing a miscellaneous chapter event.
        recurring -- either weekly, monthly, or daily occurrence
        start_date -- only set if recurring, represents start of recurrence
        end_date -- only set if recurring, represents end of recurrence
        is_recurrence -- true if event is created automatically by recurrence policy,
                         otherwise false
    """
    recurring = models.CharField(choices=RECURRENCE_CHOICES, max_length=10, default=0)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    is_recurrence = models.BooleanField(default=False)
