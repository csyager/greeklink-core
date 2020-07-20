""" models for the calendar application """

from django.db import models
from core.models import OrgEvent
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

RECURRENCE_CHOICES = [
    ('None', 'None'),
    ('Monthly', 'Monthly'),
    ('Weekly', 'Weekly'),
    ('Daily', 'Daily')
]

class ChapterEventManager(models.Manager):
    def create_chapter_event(self, name, date, time, location, recurring, start_date, end_date):
        event = self.create(name=name, date=date, time=time, location=location, recurring=recurring, start_date=start_date, end_date=end_date)
        if event.recurring == 'Monthly':
            start_date = event.start_date + relativedelta(months=+1)
            while start_date <= event.end_date:
                ChapterEvent.objects.create(name=event.name, date=start_date, time=event.time, location=event.location, 
                                            is_recurrence=True)
                start_date += relativedelta(months=+1)
        if event.recurring == 'Weekly':
            start_date = event.start_date + relativedelta(weeks=+1)
            while start_date <= event.end_date:
                ChapterEvent.objects.create(name=event.name, date=start_date, time=event.time, location=event.location, 
                                            is_recurrence=True)
                start_date += relativedelta(weeks=+1)
        if event.recurring == 'Daily':
            start_date = event.start_date + relativedelta(days=+1)
            while start_date <= event.end_date:
                ChapterEvent.objects.create(name=event.name, date=start_date, time=event.time, location=event.location, 
                                            is_recurrence=True)
                start_date += relativedelta(days=+1)

class ChapterEvent(OrgEvent):
    """ OrgEvent representing a miscellaneous chapter event.
        recurring -- either weekly, monthly, or daily occurrence
        start_date -- only set if recurring, represents start of recurrence
        end_date -- only set if recurring, represents end of recurrence
        is_recurrence -- true if event is created automatically by recurrence policy,
                         otherwise false
    """
    recurring = models.CharField(choices=RECURRENCE_CHOICES, max_length=10, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_recurrence = models.BooleanField(default=False)

    objects = ChapterEventManager()
