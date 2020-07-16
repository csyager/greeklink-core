from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from core.views import getSettings
from core.models import OrgEvent, SocialEvent
from rush.models import RushEvent
from calendar import HTMLCalendar
from datetime import datetime, timedelta
from itertools import chain

class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    def formatday(self, day, social_events, rush_events):
        social_events_per_day = social_events.filter(date__day=day)
        rush_events_per_day = rush_events.filter(date__day=day)
        d = ''
        for event in social_events_per_day:
            time = event.time.strftime("%I:%M %p").lstrip("0")
            d += f'<div class="alert alert-primary alert-calendar"><a href="/social_event{event.pk}">{ time } - { event.name }</a></div>'
        for event in rush_events_per_day:
            time = event.time.strftime("%I:%M %p").lstrip("0")
            d += f'<div class="alert alert-success alert-calendar"><a href="/rush/events/{event.pk}">{ time } - { event.name }</a></div>'
        if day != 0:
            return f"<td class='day-cell'><span class='date'>{day}</span> <div class='scrollable'>{d}</div></td>"
        return '<td></td>'

    def formatweek(self, theweek, social_events, rush_events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, social_events, rush_events)
        return f'<tr> {week} </tr>'

    def formatmonth(self, withyear=True):
        rush_events = RushEvent.objects.filter(date__month=self.month, date__year=self.year)
        social_events = SocialEvent.objects.filter(date__month=self.month, date__year=self.year)
        cal = f'<table class="table calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, social_events, rush_events)}\n'
        return cal

def index(request):
    template = loader.get_template('cal/index.html')
    d = datetime.today()
    curr_month = d.month
    curr_year = d.year
    month = int(request.GET.get('month', d.month))
    year = int(request.GET.get('year', d.year))
    if month == 13:
        month = 1
        year = year +1
    if month == 0:
        month = 12
        year = year -1
    cal = Calendar(year, month)
    context = {
        'calendar': cal.formatmonth(withyear=True),
        'cal_page': 'active',
        'settings': getSettings(), 
        'year': year,
        'curr_month': curr_month,
        'curr_year': curr_year,
        'prev_month': month -1,
        'next_month': month +1,
    }
    return HttpResponse(template.render(context, request))