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
    def create_chapter_event(self, name, date, time, location, recurring='None', end_date=None):
        event = self.create(name=name, date=date, time=time, location=location, recurring=recurring, end_date=end_date)
        if event.recurring == 'Monthly' and not event.is_recurrence:
            start_date = event.date + relativedelta(months=+1)
            while start_date <= event.end_date:
                ChapterEvent.objects.create(name=event.name, date=start_date, time=event.time, location=event.location, 
                                            recurring='Monthly', is_recurrence=True, base_event=event)
                start_date += relativedelta(months=+1)
        if event.recurring == 'Weekly' and not event.is_recurrence:
            start_date = event.date + relativedelta(weeks=+1)
            while start_date <= event.end_date:
                ChapterEvent.objects.create(name=event.name, date=start_date, time=event.time, location=event.location, 
                                            recurring='Weekly', is_recurrence=True, base_event=event)
                start_date += relativedelta(weeks=+1)
        if event.recurring == 'Daily' and not event.is_recurrence:
            start_date = event.date + relativedelta(days=+1)
            while start_date <= event.end_date:
                ChapterEvent.objects.create(name=event.name, date=start_date, time=event.time, location=event.location, 
                                            recurring='Daily', is_recurrence=True, base_event=event)
                start_date += relativedelta(days=+1)
        return event

class ChapterEvent(OrgEvent):
    """ OrgEvent representing a miscellaneous chapter event.
        recurring -- either weekly, monthly, or daily occurrence
        start_date -- only set if recurring, represents start of recurrence
        end_date -- only set if recurring, represents end of recurrence
        is_recurrence -- true if event is created automatically by recurrence policy,
                         otherwise false
    """
    recurring = models.CharField(choices=RECURRENCE_CHOICES, max_length=10, default='None')
    end_date = models.DateField(null=True, blank=True)
    is_recurrence = models.BooleanField(default=False)
    base_event = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def delete(self, *args, **kwargs):
        """ overrides delete method to fit recurrence """
        if self.recurring != 'None' and not self.is_recurrence:     # is base event
            new_base = ChapterEvent.objects.filter(base_event=self).order_by('date')[0]
            new_base.is_recurrence = False
            new_base.save()
            for event in ChapterEvent.objects.filter(base_event=self):
                event.base_event = new_base
                event.save()
        super().delete(*args, **kwargs)

    def delete_all(self, *args, **kwargs):
        """ deletes all recurrences """
        if self.is_recurrence and self.base_event is not None:
            self.base_event.delete_all()
        else:
            ChapterEvent.objects.filter(base_event=self).delete()
        super().delete(*args, **kwargs)

    objects = ChapterEventManager()
