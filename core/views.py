from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from .models import *
from .forms import *
from django.conf import settings

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from itertools import chain
from operator import attrgetter
import re, io
import base64
from django.core.files import File
import xlwt
from datetime import date, timedelta
from django.utils import timezone
from itertools import chain
from django.core.mail import send_mail
from urllib import parse
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView

# Create your views here.


def getSettings():
    settings = SiteSettings.objects.all()
    if len(settings) == 0:
        newsettings = SiteSettings()
        newsettings.save()
        settings = SiteSettings.objects.all()
    settings = settings[0]
    return settings

# index page
@login_required
def index(request):
    template = loader.get_template('core/index.html')
    date_in_two_weeks = timezone.now() + timedelta(days=14)
    date_one_day_ago = timezone.now() - timedelta(days=1)
    date_two_weeks_ago = timezone.now() - timedelta(days=14)
    social_events = SocialEvent.objects.filter(date__range=[date_one_day_ago, date_in_two_weeks])
    events = sorted(
        chain(social_events),
        key=lambda event: event.date)
    activity = Activity.objects.filter(user=request.user, date__range=[date_two_weeks_ago, timezone.now()]).order_by('date').reverse()[0:5]
    announcements = Announcement.objects.order_by('date').reverse()[0:5]
    announcement_form = AnnouncementForm()
    context = {
        "home_page": "active",
        'settings': getSettings(),
        "events": events,
        "activity": activity,
        "announcements": announcements,
        "announcement_form": announcement_form,
    }
    return HttpResponse(template.render(context, request))

# users signing up for site
def signup(request):
    template = loader.get_template('core/signup.html')
    settings = getSettings()
    verification_key = settings.verification_key
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid() and request.POST.get('verification_key') == verification_key:
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your blog account.'
            template2 = loader.get_template('core/verificationWait.html')
            context = {
                'settings': settings,
            }

            message = render_to_string('core/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            send_mail('Activate your account', message, 'admin@greeklink.com', [to_email], fail_silently=False)

            return HttpResponse(template2.render(context, request))
    else:
        form = SignupForm()
    return HttpResponse(template.render({'form': form}, request))

# users activating accounts

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        template = loader.get_template('core/verificationConfirmed.html')
        context = {
            'settings': getSettings()
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse('Activation link is invalid!')


# logs brothers out of the system
def brother_logout(request):
    logout(request)
    return HttpResponseRedirect('/login')

#------------------------------------------------ for search
class SearchView(ListView):
    template_name = 'core/search.html'
    paginate_by = 10
    
    count = 0

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['count'] = self.count or 0
        context['query'] = self.request.GET.get('query')
        context['settings'] = getSettings()
        return context
    
    def get_queryset(self):
        request = self.request
        query = request.GET.get('query', None)
        #this chains the queries together
        if query == '':
            return SocialEvent.objects.none() #just an emptyset. Honestly I have no idea why its doing an empty string rather than None but whatever when you do it this way it works
        elif (query is not None):
            SocialEvent_results = SocialEvent.objects.search(query)
            Announcement_results = Announcement.objects.search(query)
            ResourceLink_results = ResourceLink.objects.search(query)
            ResourceFile_results = ResourceFile.objects.search(query)
     
            # combine the different querysets 
            queryset_chain = chain(
                    SocialEvent_results,
                    Announcement_results,
                    ResourceLink_results,
                    ResourceFile_results
            )        
            qs = sorted(queryset_chain, 
                        key=lambda instance: instance.pk, 
                        reverse=True)
            self.count = len(qs) 
            return qs
        return SocialEvent.objects.none() # just an empty queryset as default

#------------------------------------------------------------------------------------------

@login_required
def resources(request):
    files = ResourceFile.objects.all().order_by('id')
    links = ResourceLink.objects.all()
    form = UploadFileForm()
    linkForm = LinkForm()
    settings = getSettings()
    calendar_embed = settings.calendar_embed
    context = {
        'files': files,
        'links': links,
        'form': form,
        'resources_page': 'active',
        'calendar_embed': calendar_embed,
        'linkForm': linkForm,
        'settings': settings,
    }
    template = loader.get_template('core/resources.html')
    return HttpResponse(template.render(context, request))

@staff_member_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            obj = ResourceFile()
            obj.name = form.cleaned_data['name']
            obj.description = form.cleaned_data['description']
            obj.file = form.cleaned_data['file']
            obj.extension = str(obj.file).split('.')[-1]
            obj.save()

            return HttpResponseRedirect('resources')
        else:
            return HttpResponse(form.errors)


@staff_member_required
def remove_file(request, file_id):
    ResourceFile.objects.get(id=file_id).delete()
    return HttpResponseRedirect('resources')


@staff_member_required
def addCal(request):
    settings = getSettings()
    settings.calendar_embed = request.POST['cal_embed_link']
    settings.save()
    return HttpResponseRedirect('resources')


@staff_member_required
def removeCal(request):
    settings = getSettings()
    settings.calendar_embed = ""
    settings.save()
    return HttpResponseRedirect('resources')


@login_required
def social(request):
    template = loader.get_template('core/social.html')
    events = SocialEvent.objects.all().order_by('-date')
    context = {
        'settings': getSettings(),
        'social_page': "active",
        'events': events,
    }
    return HttpResponse(template.render(context, request))


@staff_member_required
def create_social_event(request):
    if request.method == 'POST':
        obj = SocialEvent()
        obj.name = request.POST.get('name')
        obj.date = request.POST.get('date')
        obj.time = request.POST.get('time')
        obj.location = request.POST.get('location')
        obj.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def social_event(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    context = {
        'event': event,
        'settings': getSettings(),
        'social_page': "active",
    }
    template = loader.get_template('core/social_event.html')
    return HttpResponse(template.render(context, request))


@staff_member_required
def remove_social_event(request, event_id):
    SocialEvent.objects.filter(id=event_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def add_to_list(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    if request.method == 'POST' and not event.party_mode:
        multiple_names_value = request.POST.get('multiple_names')
        user = request.user.get_full_name()
        user_count = len(event.list.filter(user = user))
        num_adding = len(multiple_names_value.splitlines())
        if request.POST.get("name") != "":
            num_adding += 1
        if event.list_limit != -1 and user_count + num_adding > event.list_limit:
            messages.error(request, "list limit exceeded")
        else: 
            for line in multiple_names_value.splitlines():
                attendee = Attendee()
                attendee.name = line
                attendee.user = user
                try:
                    with transaction.atomic():
                        attendee.save()
                        event.list.add(attendee)
                except(IntegrityError):
                    messages.error(request, line)


            individual_name_value = request.POST.get('name')
            if individual_name_value != "":    
                attendee = Attendee()
                attendee.name = request.POST.get('name')
                attendee.user = user
                try:
                    with transaction.atomic():
                        attendee.save()
                        event.list.add(attendee)
                except(IntegrityError):
                    messages.error(request, attendee.name)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def remove_from_list(request, event_id, attendee_id):
    event = SocialEvent.objects.get(id=event_id)
    if not event.party_mode:
        attendee = Attendee.objects.get(id=attendee_id)
        event.list.remove(attendee)
        attendee.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def check_attendee(request):
    attendee_id = request.GET.get('attendee_id', None)
    attendee = Attendee.objects.get(id=attendee_id)
    if attendee.attended == False:
        attendee.attended = True
    else:
        attendee.attended = False
    attendee.save()
    data = {
        'attended': attendee.attended
    }
    return JsonResponse(data)

@login_required
def refresh_attendees(request):
    event_id = int(request.GET.get('event_id', None))
    event = SocialEvent.objects.get(id=event_id)
    data = {}
    for attendee in event.list.all():
        data.update({attendee.id: attendee.attended})
    return JsonResponse(data)

@staff_member_required
def toggle_party_mode(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    if(event.party_mode):
        event.party_mode = False
    else:
        event.party_mode = True
    event.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@staff_member_required
def clear_list(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    for attendee in event.list.all():
        event.list.remove(attendee)
        attendee.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@staff_member_required
def export_xls(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + str(event_id) + '_attendance.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Attendance')
    row_num = 0
    font_style=xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Name']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows = event.list.all().values_list('name')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


@staff_member_required
def remove_link(request, link_id):
    link = ResourceLink.objects.get(id=link_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@staff_member_required
def add_link(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            obj = ResourceLink()
            obj.name = form.cleaned_data['name']
            obj.description = form.cleaned_data['description']
            obj.url = form.cleaned_data['url']
            obj.save()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponse(form.errors)


@staff_member_required
def add_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            obj = Announcement()
            obj.title = form.cleaned_data['title']
            obj.target = form.cleaned_data['target']
            obj.user = request.user
            obj.body = form.cleaned_data['body']
            obj.save()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponse(form.errors)
