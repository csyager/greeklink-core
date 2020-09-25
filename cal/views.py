from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from core.views import getSettings
from core.models import OrgEvent, SocialEvent
from rush.models import RushEvent
from cal.models import ChapterEvent
from calendar import HTMLCalendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from itertools import chain
from django.contrib.auth.decorators import login_required, permission_required
from .forms import ChapterEventForm
from organizations.models import Client
from tenant_schemas.utils import tenant_context
from django.contrib import messages

class Calendar(HTMLCalendar):
    def __init__(self, request, year=None, month=None):
        self.year = year
        self.month = month
        self.request = request
        super(Calendar, self).__init__()

    def formatday(self, day, social_events, rush_events, chapter_events):
        if not self.request.user_agent.is_mobile:
            social_events_per_day = social_events.filter(date__day=day)
            rush_events_per_day = rush_events.filter(date__day=day)
            chapter_events_per_day = chapter_events.filter(date__day=day)
            public_social_events_per_day = []
            public_chapter_events_per_day = []
            org_community = self.request.tenant.community
            if org_community is not None:
                for tenant in Client.objects.filter(community=org_community).exclude(name=self.request.tenant.name).all():
                    with tenant_context(tenant):
                        for event in SocialEvent.objects.filter(is_public=True, date__month=self.month, date__year=self.year, date__day=day):
                            public_social_events_per_day.append((event, tenant.name))
                        for event in ChapterEvent.objects.filter(is_public=True, date__month=self.month, date__year=self.year, date__day=day):
                            public_chapter_events_per_day.append((event, tenant.name))
            d = ''
            for event in social_events_per_day:
                time = event.time.strftime("%I:%M %p").lstrip("0")
                d += f'<div class="alert alert-primary alert-calendar"><a href="/social_event{event.pk}">{ time } - { event.name }</a></div>'
            for event in rush_events_per_day:
                time = event.time.strftime("%I:%M %p").lstrip("0")
                d += f'<div class="alert alert-success alert-calendar"><a href="/rush/events/{event.pk}">{ time } - { event.name }</a></div>'
            for event in chapter_events_per_day:
                time = event.time.strftime("%I:%M %p").lstrip("0")
                d += f'<div class="alert alert-secondary alert-calendar"><a href="" data-toggle="modal" data-target="#detailModal_{ event.pk }">{ time } - { event.name }</a></div>'
            for event in public_social_events_per_day:
                time = event[0].time.strftime("%I:%M %p").lstrip("0")
                d += f'<div class="alert alert-info alert-calendar">{ time } - { event[1] }\'s { event[0].name }</div>'
            for event in public_chapter_events_per_day:
                time = event[0].time.strftime("%I:%M %p").lstrip("0")
                d += f'<div class="alert alert-info alert-calendar"> { time } - { event[1] }\'s { event[0].name }</div>'
            if day != 0 and d != '':
                return f"<td class='day-cell table-active'><span class='date'><a href='/cal/date/{self.year}/{self.month}/{day}'>{day}</a></span> <div class='scrollable'>{d}</div></td>"
            elif day != 0:
                return f"<td class='day-cell'><span class='date'><a href='/cal/date/{self.year}/{self.month}/{day}'>{day}</a></span> <div class='scrollable'>{d}</div></td>"
        else:
            has_events = social_events.filter(date__day=day) or rush_events.filter(date__day=day) or chapter_events.filter(date__day=day)
            if day != 0 and has_events:
                return f"<td class='day-cell table-active'><span class='date'><a href='/cal/date/{self.year}/{self.month}/{day}'>{day}</a></span>"
            elif day != 0:
                return f"<td class='day-cell'><span class='date'><a href='/cal/date/{self.year}/{self.month}/{day}'>{day}</a></span>"
        return '<td></td>'

    def formatweek(self, theweek, social_events, rush_events, chapter_events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, social_events, rush_events, chapter_events)
        return f'<tr> {week} </tr>'

    def formatmonth(self, withyear=True):
        rush_events = RushEvent.objects.filter(date__month=self.month, date__year=self.year)
        social_events = SocialEvent.objects.filter(date__month=self.month, date__year=self.year)
        chapter_events = ChapterEvent.objects.filter(date__month=self.month, date__year=self.year)
        cal = f'<table class="table calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, social_events, rush_events, chapter_events)}\n'
        return cal

@login_required
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
    cal = Calendar(request, year, month)
    cal.setfirstweekday(6)  # sets sunday to be the first day of the week to show on the calendar
    context = {
        'calendar': cal.formatmonth(withyear=True),
        'cal_page': 'active',
        'settings': getSettings(),
        'year': year,
        'curr_month': curr_month,
        'curr_year': curr_year,
        'prev_month': month -1,
        'next_month': month +1,
        'event_form': ChapterEventForm(),
        'chapter_events': ChapterEvent.objects.filter(date__month=month),
    }
    return HttpResponse(template.render(context, request))

@login_required
def date(request, year, month, day):
    template = loader.get_template('cal/date.html')
    this_date = datetime(year, month, day)
    social_events = SocialEvent.objects.filter(date=this_date)
    rush_events = RushEvent.objects.filter(date=this_date)
    chapter_events = ChapterEvent.objects.filter(date=this_date)
    public_social_events = []
    public_chapter_events = []
    org_community = request.tenant.community
    for tenant in Client.objects.filter(community=org_community).exclude(name=request.tenant.name).exclude(name='public').all():
                with tenant_context(tenant):
                    for event in SocialEvent.objects.filter(is_public=True, date=this_date):
                        public_social_events.append((event, tenant.name))
                    for event in ChapterEvent.objects.filter(is_public=True, date=this_date):
                        public_chapter_events.append((event, tenant.name))
    all_events = sorted(
        chain(social_events, rush_events, chapter_events),
        key=lambda instance: instance.time
    )
    community_events = sorted(
        chain(public_social_events, public_chapter_events),
        key=lambda instance: instance[0].time
    )
    context = {
        'settings': getSettings(),
        'cal_page': 'active',
        'today': datetime.today(),
        'date': this_date.strftime('%B %d, %Y').lstrip("0"),
        'social_events': social_events,
        'rush_events': rush_events,
        'chapter_events': chapter_events,
        'all_events': all_events,
        'community_events': community_events,
        'next_date': this_date + timedelta(days=1),
        'prev_date': this_date - timedelta(days=1)
    }
    return HttpResponse(template.render(context, request))

@permission_required('cal.add_chapterevent')
def create_chapter_event(request):
    if request.method == 'POST':
        form = ChapterEventForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            date = form.cleaned_data.get('date')
            time = form.cleaned_data.get('time')
            location = form.cleaned_data.get('location')
            is_public = form.cleaned_data.get('public')
            recurring = form.cleaned_data.get('recurring')
            end_date = form.cleaned_data.get('end_date')

            ChapterEvent.objects.create_chapter_event(name, date, time, is_public, location, recurring, end_date)
            messages.success(request, "Chapter event " + name + " has been created successfully.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponse(form.errors)
    else:
        raise Http404

@permission_required('cal.delete_chapterevent')
def delete_chapter_event(request, event_id):
    ChapterEvent.objects.get(pk=event_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@permission_required('cal.delete_chapterevent')
def delete_chapter_event_recursive(request, event_id):
    ChapterEvent.objects.get(pk=event_id).delete_all()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@permission_required('cal.change_chapterevent')
def edit_chapter_event(request, event_id):
    """ edits a single chapter event by deleting it and recreating it with different parameters.
        any events that use this event as a base_event are updated to use the new event instead
        event_id -- primary key of event being edited
    """
    if request.method == "POST":
        if request.POST.get('action') == 'singular':
            old_event = ChapterEvent.objects.get(pk=event_id)
            child_events = old_event.children
            old_event.delete()
            name = request.POST.get('name')
            date = datetime.strptime(request.POST.get('date'), "%Y-%m-%d").date()
            time = request.POST.get('time')
            location = request.POST.get('location')
            if request.POST.get('public') == 'on':
                is_public = True
            else:
                is_public = False
            recurring = request.POST.get('recurring')
            end_date = datetime.strptime(request.POST.get('end_date'), "%Y-%m-%d").date()
            new_event = ChapterEvent.objects.create(name=name, date=date, time=time, is_public=is_public, location=location, recurring=recurring, end_date=end_date)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            ChapterEvent.objects.get(pk=event_id).delete_all()
            name = request.POST.get('name')
            date = datetime.strptime(request.POST.get('date'), "%Y-%m-%d").date()
            time = request.POST.get('time')
            location = request.POST.get('location')
            if request.POST.get('public') == 'on':
                is_public = True
            else:
                is_public = False
            recurring = request.POST.get('recurring')
            end_date = datetime.strptime(request.POST.get('end_date'), "%Y-%m-%d").date()
            ChapterEvent.objects.create_chapter_event(name=name, date=date, time=time, is_public=is_public, location=location, recurring=recurring, end_date=end_date)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        raise Http404
