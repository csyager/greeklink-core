from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, HttpResponseNotFound
from django.template import loader, RequestContext

from .models import *
from .forms import *
from .tokens import *
from django.conf import settings

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
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
import logging
import requests
from django.core.files import File
import xlwt
from datetime import date, timedelta
from django.utils import timezone
from itertools import chain
from django.core.mail import get_connection, send_mail, send_mass_mail, BadHeaderError
from urllib import parse
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
import datetime
from django.contrib.auth.views import LoginView
from django.dispatch import receiver
from organizations.models import Client
from rush.models import RushEvent
from cal.models import ChapterEvent
# Create your views here.

def getSettings():
    """ utility function for returning SiteSettings object.  SiteSettings
        should be a singular database object representing base settings for
        the site.  This function makes sure the database object remains
        singular.  Should be called in context variables of every page
    """
    # pylint: disable=function-redefined, invalid-name, redefined-outer-name
    settings = SiteSettings.objects.all()
    if len(settings) == 0:
        newsettings = SiteSettings(pk=1)
        newsettings.save()
        settings = SiteSettings.objects.all()
    settings = settings[0]
    return settings

def health(request):
    """ for aws health checks, just prints a success message
    """
    if settings.EC2_PRIVATE_IP:
        logging.info(f"Getting client for health checks.")
        c = Client.objects.get(name='health')
        logging.info(f"health client: {c}")
        c.domain_url = settings.EC2_PRIVATE_IP
        c.save()
        c = Client.objects.get(name='health')
        logging.info(f"health client IP set to {c.domain_url}")
    response = requests.get("http://169.254.169.254/latest/meta-data/instance-id")
    return HttpResponse(response.content)

# extends built in Django LoginView
class CustomLoginView(LoginView):
    def get(self, request, *args, **kwargs):
        current_site = request.tenant.name
        if current_site != 'public':
            return super(CustomLoginView, self).get(request, *args, **kwargs)
        else:
            template = loader.get_template('core/communities.html')
            context = {
                'form': OrganizationSelectForm,
            }
            return HttpResponse(template.render(context, request))
    def post(self, request, *args, **kwargs):
        current_site = request.tenant.name
        if current_site != 'public':
            return super(CustomLoginView, self).post(request, *args, **kwargs)
        else:
            try:
                port = ':' + request.build_absolute_uri('/').split(':')[2]
            except IndexError:
                port = ''
            redirect_tenant_url = request.POST.get('organization')
            return HttpResponseRedirect("http://" + redirect_tenant_url + port)

# index page
@login_required
def index(request):
    template = loader.get_template('core/index.html')
    date_in_two_weeks = timezone.now() + timedelta(days=14)
    date_one_day_ago = timezone.now() - timedelta(days=1)
    date_two_weeks_ago = timezone.now() - timedelta(days=14)
    social_events = SocialEvent.objects.filter(date__range=[date_one_day_ago, date_in_two_weeks])
    rush_events = RushEvent.objects.filter(date__range=[date_one_day_ago, date_in_two_weeks])
    chapter_events = ChapterEvent.objects.filter(date__range=[date_one_day_ago, date_in_two_weeks])
    events = sorted(
        chain(social_events, rush_events, chapter_events),
        key=lambda event: (event.date, event.time))
     
    first_five_events = events[:5]
    remainder_events = events[5:]

    announcements = Announcement.objects.order_by('-date')
    announcement_form = AnnouncementForm()

    #for pagination
    paginator = Paginator(announcements, 5)                                               #this number changes items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    announcementscount = len(announcements)

    context = {
        "home_page": "active",
        'settings': getSettings(),
        "announcements": announcements,
        "announcement_form": announcement_form,
        'page_obj': page_obj,
        'first_five_events': first_five_events,
        'remainder_events': remainder_events,
        'announcementscount' : announcementscount
    }
    return HttpResponse(template.render(context, request))

def get_tenant_domain(request, domain_url):
    try:
        port = ':' + request.build_absolute_uri('/').split(':')[2].strip('/')
    except IndexError:
        port = ''
    return domain_url + port

# users signing up for site
def signup(request):
    template = loader.get_template('core/signup.html')
    site_settings = getSettings()
    verification_key = site_settings.verification_key
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid() and request.POST.get('verification_key') == verification_key:
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = request.tenant
            mail_subject = 'Activate your Greek-Rho account.'
            template2 = loader.get_template('core/verificationWait.html')
            context = {
                'settings': site_settings,
                'user': user,
            }

            message = render_to_string('core/acc_active_email.html', {
                'user': user,
                'domain': get_tenant_domain(request, current_site.domain_url),
                'uid': user.pk,
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            send_mail('Activate your account', message, settings.VERIFY_EMAIL_USER, [to_email], fail_silently=False, auth_user=settings.VERIFY_EMAIL_USER)

            return HttpResponse(template2.render(context, request))
    else:
        form = SignupForm()
    return HttpResponse(template.render({'form': form}, request))

def resend_verification_email(request, user_id):
    template = loader.get_template('core/verificationWait.html')
    user = User.objects.get(id=user_id)
    mail_subject = 'Activate your Greek-Rho account.'

    context = {
            'settings': getSettings(),
            'user': user,
        }

    message = render_to_string('core/acc_active_email.html', {
        'user': user,
        'domain': get_tenant_domain(request, request.tenant.domain_url),
        'uid': user.pk,
        'token': account_activation_token.make_token(user),
    })
    to_email = user.email
    send_mail('Activate your account', message, settings.VERIFY_EMAIL_USER, [to_email], fail_silently=False, auth_user=settings.VERIFY_EMAIL_USER)
    
    messages.success(request, "Email has been resent to " + to_email)
    return HttpResponse(template.render(context, request))

# users activating accounts

def activate(request, user_id, token):
    try:
        uid = user_id
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

# forgot credentials page
def forgot_credentials(request):
    if request.method == 'POST':
        form = ForgotCredentialsForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=email)
            except User.MultipleObjectsReturned:
                messages.error(request, "Multiple accounts exist with the same email address.  Contact your site administrator for assistance.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            mail_subject = "Reset your password"
            message = render_to_string('core/reset_credentials_email.html', {
                'user': user,
                'domain': get_tenant_domain(request, request.tenant.domain_url),
                'uid': user.pk,
                'token': account_activation_token.make_token(user),
            })
            send_mail(mail_subject, message, settings.VERIFY_EMAIL_USER, [email], fail_silently=False, auth_user=settings.VERIFY_EMAIL_USER)
            messages.success(request, "Email with password reset link has been sent.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:    
        template = loader.get_template('core/forgot_credentials.html')
        context = {
            'settings': getSettings(),
            'form': ForgotCredentialsForm(),
        }
        return HttpResponse(template.render(context, request))


def reset_password(request, user_id, token):
    user = User.objects.get(pk=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data.get('new_password1')
            password2 = form.cleaned_data.get('new_password2')
            if password1 == password2:
                user.set_password(password1)
                user.save()
                template = loader.get_template('core/reset_password_success.html')
                context = {
                    'settings': getSettings()
                }
                return HttpResponse(template.render(context, request))
        else:   # fields did not match
            for field in form:
                for error in field.errors:
                    messages.error(request, error)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    elif account_activation_token.check_token(user, token):
        template = loader.get_template('core/reset_password.html')
        context = {
            'settings': getSettings(),
            'form': SetPasswordForm()   # pylint: disable=no-value-for-parameter
        }
        return HttpResponse(template.render(context, request))
    
    else:
        return HttpResponse("Invalid token!")

# logs brothers out of the system
def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/login')

# ------------------ ERRORS ---------------------
def handler404(request, exception):
    try:
        context = {
            'settings': getSettings()
        }
        template = loader.get_template('core/404.html')
        return HttpResponseNotFound(template.render(context, request), status=404)
    except:
        return HttpResponseNotFound(exception)

def handler500(request):
    settings = getSettings()
    context = {
        'settings': getSettings(),
    }
    template = loader.get_template('core/500.html')
    return HttpResponseServerError(template.render(context, request))

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
            return SocialEvent.objects.none() # just an emptyset. Honestly I have no idea why its doing an empty string rather than None but whatever when you do it this way it works
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

@permission_required('core.add_resourcefile')
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
            messages.success(request, "File " + obj.name + " has been successfully uploaded.")
            return HttpResponseRedirect('resources')
        else:
            return HttpResponse(form.errors)


@permission_required('core.delete_resourcefile')
def remove_file(request, file_id):
    obj = ResourceFile.objects.get(id=file_id)
    name = obj.name
    obj.file.delete()
    obj.delete()
    messages.success(request, "File " + name + " has been successfully deleted.")
    return HttpResponseRedirect('resources')


@permission_required('core.add_calendar')
def addCal(request):
    settings = getSettings()
    settings.calendar_embed = request.POST['cal_embed_link']
    settings.save()
    return HttpResponseRedirect('resources')


@permission_required('core.delete_calendar')
def removeCal(request):
    settings = getSettings()
    settings.calendar_embed = ""
    settings.save()
    return HttpResponseRedirect('resources')


@login_required
def social(request):
     
    template = loader.get_template('core/social.html')

    now = datetime.datetime.now()
    upcoming = SocialEvent.objects.filter(date__gte=now).order_by('date', 'time')   #today, then tomorrow, tomorrow + 1
    past = SocialEvent.objects.filter(date__lt=now).order_by('-date', '-time')      #yesterday, day before yesterday

    events = chain(upcoming, past)
    events = list(events)                                                           #converts to list, necessary for paginator
    # events = SocialEvent.objects.all().order_by('-date', 'time')                  lets keep this just in case something goes wrong with the query chain
    rosters = list(Roster.objects.all())

    # event pagination
    event_paginator = Paginator(events, 10)                                               #this number changes items per page
    event_page_number = request.GET.get('eventspage')
    event_page_obj = event_paginator.get_page(event_page_number)
    eventscount = len(events)
    upcoming_list = list(filter(lambda el: el in upcoming, event_page_obj))
    past_list = list(filter(lambda el: el in past, event_page_obj))

    # roster pagination
    roster_paginator = Paginator(rosters, 10)
    roster_page_number = request.GET.get('rosterspage')
    roster_page_obj = roster_paginator.get_page(roster_page_number)
    rosterscount = len(rosters)
    
    try:
        show_tab = request.session['social_tab']
    except KeyError:
        show_tab = 'events'

    context = {
        'settings': getSettings(),
        'social_page': "active",
        'event_page_obj': event_page_obj,
        'upcoming_events': upcoming_list,
        'past_events': past_list,
        'eventscount' : eventscount,
        'rosters': rosters,
        'roster_page_obj': roster_page_obj,
        'rosterscount': rosterscount,
        'social_event_form': SocialEventForm,
        'show_tab': show_tab
    }
    return HttpResponse(template.render(context, request))


@login_required
def update_social_tab_session(request):
    request.session['social_tab'] = request.GET.get('social_tab')
    return HttpResponse()


@permission_required('core.add_socialevent')
def create_social_event(request):
    if request.method == 'POST':
        form = SocialEventForm(request.POST)
        event = SocialEvent()
        if form.is_valid():
            event.name = form.cleaned_data['name']
            event.date = form.cleaned_data['date']
            event.time = form.cleaned_data['time']
            event.location = form.cleaned_data['location']
            if form.cleaned_data['public']:
                event.is_public = True
            else:
                event.is_public = False
            if form.cleaned_data['list_limit'] != '' and form.cleaned_data['list_limit'] != None:
                event.list_limit = form.cleaned_data['list_limit']
            else:
                event.list_limit = -1
            event.save()
            messages.success(request, "Social event " + event.name + " has been successfully created.")
        else:
            errors = ""
            for field in form:
                for error in field.errors:
                    errors += error
            messages.error(request, "Social event could not be created, because of the following errors: ")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@permission_required('core.change_socialevent')
def edit_social_event(request, event_id):
    if request.method == 'POST':
        obj = SocialEvent.objects.get(id=event_id)
        obj.name = request.POST.get('name')
        obj.date = request.POST.get('date')
        obj.time = request.POST.get('time')
        obj.location = request.POST.get('location')
        if request.POST.get('public') == 'on':
            obj.is_public = True
        else:
            obj.is_public = False
        if request.POST.get('limit') != None:
            if request.POST.get('limit') != '':
                obj.list_limit = request.POST.get('limit')
            else:
                obj.list_limit = -1
        else:
            obj.list_limit = -1
        obj.save()
        messages.success(request, "Social event " + obj.name + " has been successfully edited.")

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


@permission_required('core.delete_socialevent')
def remove_social_event(request, event_id):
    name = SocialEvent.objects.get(id=event_id).name
    try:
        SocialEvent.objects.get(id=event_id).delete()
        messages.success(request, "Social Event " + name + " has been successfully deleted.")
    except Exception as e:
        messages.error(request, "Social event could not be deleted: " + e)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def roster(request, roster_id):
    roster = Roster.objects.get(id=roster_id)
    events = SocialEvent.objects.all()
    context = {
        'settings': getSettings(),
        'social_page': "active",
        'roster': roster,
        'events': events,
    }
    template = loader.get_template('core/roster.html')    
    return HttpResponse(template.render(context, request))

@permission_required('core.change_roster')
def edit_roster(request, roster_id):
    if request.method == 'POST':
        roster = Roster.objects.get(id=roster_id)
        updated_members = request.POST.get('updated_members')
        roster.members.all().delete()
        for line in updated_members.splitlines():
            if line != "":
                member = RosterMember()
                member.name = line
                member.roster = roster
                try:
                    with transaction.atomic():
                        member.save()
                except IntegrityError:
                        messages.error(request, line)
        roster.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        raise Http404

@permission_required('core.change_roster')
def remove_from_roster(request, roster_id, member_id):
    roster = Roster.objects.get(id=roster_id)
    member = roster.members.get(pk=member_id)
    name = member.name
    member.delete()
    roster.save()
    messages.success(request, name + " has been successfully removed from Roster " + roster.title + ".", extra_tags='successful_remove')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@permission_required('core.change_roster')
def add_roster_to_events(request, roster_id):
    if request.method == 'POST':
        roster = Roster.objects.get(id=roster_id)
        user = request.user.get_full_name()
        events = request.POST.getlist('event_checkboxes')
        for event in events:
            event_obj = SocialEvent.objects.get(name=event)
            for member in roster.members.all():
                attendee = Attendee()
                attendee.name = member.name
                attendee.user = user
                attendee.event = event_obj
                try:
                    with transaction.atomic():
                        attendee.save()
                except(IntegrityError):
                    continue
            messages.success(request, event)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:
        raise Http404
    

@permission_required('core.delete_announcement')
def remove_announcement(request, announcement_id):
    Announcement.objects.filter(id=announcement_id).delete()
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
            messages.error(request, event.list_limit, extra_tags="limit")
        else: 
            for line in multiple_names_value.splitlines():
                if line != "":
                    attendee = Attendee()
                    attendee.name = line
                    attendee.user = user
                    attendee.event = event
                    try:
                        with transaction.atomic():
                            attendee.save()
                    except(IntegrityError):
                        messages.error(request, line, extra_tags='duplicate')


            individual_name_value = request.POST.get('name')
            if individual_name_value != "":    
                attendee = Attendee()
                attendee.name = request.POST.get('name')
                attendee.user = user
                attendee.event = event
                try:
                    with transaction.atomic():
                        attendee.save()
                except(IntegrityError):
                    messages.error(request, attendee.name, extra_tags='duplicate')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def remove_from_list(request, event_id, attendee_id):
    event = SocialEvent.objects.get(id=event_id)
    if not event.party_mode:
        attendee = Attendee.objects.get(id=attendee_id)
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

@permission_required('core.change_socialevent')
def toggle_party_mode(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    if(event.party_mode):
        event.party_mode = False
    else:
        event.party_mode = True
    event.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@permission_required('core.change_socialevent')
def clear_list(request, event_id):
    event = SocialEvent.objects.get(id=event_id)
    for attendee in event.list.all():
        attendee.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@permission_required('core.change_socialevent')
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

@permission_required('core.add_roster')
def save_as_roster(request, event_id):
    if request.method == 'POST':
        event = SocialEvent.objects.get(id=event_id)
        roster_name = request.POST.get('roster_name')
        roster = Roster.objects.create(title=roster_name)
        for attendee in event.list.all():
            name = attendee.name
            member = RosterMember.objects.create(name=name, roster=roster)
            member.save()
        roster.save()
        messages.success(request, "List successfully saved as roster: " + roster_name)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    else:
        raise Http404


@permission_required('core.add_roster')
def create_roster(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        members = request.POST.get('members').splitlines()
        roster = Roster.objects.create(title=title)
        for member in members:
            try:
                with transaction.atomic():
                    RosterMember.objects.create(name=member, roster=roster)
            except IntegrityError:
                continue
        roster.save()
        messages.success(request, "Roster " + title + " has been successfully created.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseNotFound(request)

@permission_required('core.delete_roster')
def remove_roster(request, roster_id):
    r = Roster.objects.get(pk=roster_id)
    name = r.title
    r.delete()
    messages.success(request, "Roster " + name + " has been successfully deleted.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@permission_required('core.delete_resourcelink')
def remove_link(request, link_id):
    link = ResourceLink.objects.get(id=link_id)
    name = link.name
    link.delete()
    messages.success(request, "Link " + name + " has been successfully deleted.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@permission_required('core.add_resourcelink')
def add_link(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            obj = ResourceLink()
            obj.name = form.cleaned_data['name']
            obj.description = form.cleaned_data['description']
            obj.url = form.cleaned_data['url']
            obj.save()
            messages.success(request, "Link " + obj.name + " has been successfully added.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponse(form.errors)


@permission_required('core.add_announcement')
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
            
            if 'send_emailBoolean' in request.POST:
                send_emailBoolean = request.POST['send_emailBoolean']
            else:
                send_emailBoolean = False
            if send_emailBoolean:
                
                truemessage = render_to_string('core/announcement_email.html', {
                    'user': request.user.first_name + request.user.last_name,
                    'body': form.cleaned_data['body'],
                    'target': form.cleaned_data['target']
                })
                message_list = []
                for user in User.objects.all():
                    if user.email != '': 
                        message_list.append((obj.title, truemessage, settings.ANN_EMAIL, [user.email]))

                send_mass_mail(message_list, fail_silently=True, auth_user=settings.ANN_EMAIL)

                messages.success(request, "Announcement has been successfully posted and users have been notified via email.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                
            else:
                messages.success(request, "Announcement has been successfully posted.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            error_string = "Announcement was not successfully posted, because of the following errors:  "
            for field in form:
                for error in field.errors:
                    error_string += error + '  '
            messages.error(request, error_string)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def support_request(request):
    context = {
            'settings': getSettings(),
            'supportform': SupportForm(),
        }
    if request.method == 'GET':
        template = loader.get_template('core/support.html')
        
        return HttpResponse(template.render(context, request))
    else:
        supportform = SupportForm(request.POST)
        if supportform.is_valid():
            subject = supportform.cleaned_data['subject']
            from_email = supportform.cleaned_data['from_email']
            message = supportform.cleaned_data['message']

            truemessage = render_to_string('core/support_email.html', {
                'from_email': from_email,
                'message': message,
            })

            template2 = loader.get_template('core/supportConfirmation.html')
            
            try:
                send_mail(subject, truemessage, settings.SUPPORT_EMAIL_USER, ['Greeklink@virginia.edu'], auth_user=settings.SUPPORT_EMAIL_USER)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return HttpResponse(template2.render(context, request))
        else:
            template = loader.get_template('core/support.html')
            context = {
                'settings': getSettings(),
                'supportform': supportform
            }
    return HttpResponse(template.render(context, request))

#announcements page
def announcement(request, announcement_id):
    announcement = Announcement.objects.get(id=announcement_id)
    context = {
        'announcement': announcement,
        'settings': getSettings(),
    }
    template = loader.get_template('core/announcement.html')
    return HttpResponse(template.render(context, request))
