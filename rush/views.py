""" views corresponding to rush/urls.py """

import re
import io
import base64
from urllib import parse
from django.core.files import File
from django.template import loader
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from core.views import getSettings
from .forms import CommentForm, RusheeForm
from .models import Rushee, RushEvent, Comment

# Create your views here.
@login_required
def rushee(request, num):
    """ rushee profile page
        num -- primary key of the rushee being viewed
    """
    template = loader.get_template('rush/rushee.html')
    obj = Rushee.objects.get(id=num)
    all_events = RushEvent.objects.all().order_by('date')
    try:
        comments = Comment.objects.filter(rushee=obj)
    except Comment.DoesNotExist:
        comments = None
    form = CommentForm()
    current_round = obj.round

     # get next rushee
    referer = request.META.get('HTTP_REFERER')
    path = parse.urlparse(referer).path
    if 'search' not in path:
        try:
            next_rushee = (Rushee.objects.filter(name__gt=obj.name, cut=0, round=current_round)
                           .order_by('name')[0].id)
            next_url = '/rush/rushee' + str(next_rushee)
        except IndexError:
            next_url = ""

        try:
            prev_rushee = (Rushee.objects.filter(name__lt=obj.name, cut=0, round=current_round)
                           .order_by('-name')[0].id)
            prev_url = '/rush/rushee' + str(prev_rushee)
        except IndexError:
            prev_url = ""

    else:
        next_url = ""

    context = {
        "rushee": obj,
        "comments": comments,
        "form": form,
        "events": all_events,
        'settings': getSettings(),
        'next_url': next_url,
        'prev_url': prev_url,
        'rush_page': 'active'
    }
    return HttpResponse(template.render(context, request))


# adds a rushee to the database when they first sign in
@login_required
def register(request, event_id):
    """ adds a rushee to the database when they first sign in
        event_id -- primary key of event that rushee is registering in
    """
    form = RusheeForm(request.POST)
    if form.is_valid():
        obj = Rushee()
        obj.name = form.cleaned_data['name']
        obj.email = form.cleaned_data['email']
        obj.year = form.cleaned_data['year']
        obj.major = form.cleaned_data['major']
        obj.hometown = form.cleaned_data['hometown']
        obj.address = form.cleaned_data['address']
        obj.phone_number = form.cleaned_data['phone_number']

        # NOTE: Please don't mess with this, I don't know how I made it work
        # Handles saving the image as a file in media/profile_images
        # and then storing them as a model field for Rushees
        data_url_pattern = re.compile('data:image/png;base64,(.*)$')
        image_data = request.POST.get('profile_picture_data')
        # try/catch: catches error thrown if picture data not inputted
        try:
            image_data = data_url_pattern.match(image_data).group(1)
            image_data = bytes(image_data, 'UTF-8')
            image_data = base64.b64decode(image_data)
            img_io = io.BytesIO(image_data)
            # immoralize this line for all time as the line that made our first
            # rush session take 7 hours instead of 4
            # obj.profile_picture_data = image_data

            obj.profile_picture.save(str(obj.id) + '.png', File(img_io))
            obj.save()
        except AttributeError:
            obj.save()

        this_event = RushEvent.objects.get(id=event_id)
        this_event.attendance.add(obj)
        this_event.save()

        template = loader.get_template('rush/register.html')
        context = {
            "name": obj.name,
            "event_id": event_id,
            'settings': getSettings(),
            'rush_page': 'active'
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse(form.errors.as_data())


# for rushees signing into events
@login_required
def signin(request, event_id=-1):
    """ page for rushees signing into events when they are already registered
        event_id -- if passed in URL represents the event being signed into
                    if not passed, defaults to -1 meaning first event
    """
    template = loader.get_template('rush/signin.html')
    form = RusheeForm()
    objects = Rushee.objects.filter(cut=0).order_by('name')
    all_events = RushEvent.objects.all().order_by('date')
    if int(event_id) != -1:
        this_event = RushEvent.objects.get(id=int(event_id))
        objects = (Rushee.objects.filter(round=event.round, cut=0)
                   .exclude(rushevent=event).order_by('name'))
    else:
        this_event = events.first()
    context = {
        "rush_page": "active",
        "form": form,
        "event": this_event,
        "objects": objects,
        "events": all_events,
        'settings': getSettings()
    }
    return HttpResponse(template.render(context, request))


# is submitted when a rushee signs into an event
@login_required
def attendance(request, rushee_id, event_id):
    """ update database with attendance when a rushee signs into an event
        rushee_id -- primary key of rushee
        event_id -- primary key of event rushee is attending
    """
    template = loader.get_template('rush/register.html')
    obj = Rushee.objects.get(id=rushee_id)
    this_event = RushEvent.objects.get(id=event_id)
    this_event.attendance.add(obj)
    this_event.save()
    name = obj.name.split()[0]
    context = {
        "name": name,
        "event_id": event_id,
        'settings': getSettings(),
        'rush_page': 'active'
    }
    return HttpResponse(template.render(context, request))


@login_required
def events(request):
    """ page showing all Rush Events """
    template = loader.get_template('rush/events.html')
    all_events = RushEvent.objects.all().order_by('date')
    settings = getSettings()
    round_range = range(1, settings.num_rush_rounds + 1)
    context = {
        'settings': settings,
        'round_range': round_range,
        'events': all_events,
        'rush_page': "active",
    }

    return HttpResponse(template.render(context, request))

@login_required
def event(request, event_id):
    """ page showing single rush event details
        event_id -- primary key of event
    """
    this_event = RushEvent.objects.get(id=event_id)
    context = {
        'event': this_event,
        'settings': getSettings(),
        'rush_page': 'active',
    }
    template = loader.get_template('rush/event.html')
    return HttpResponse(template.render(context, request))


@staff_member_required
def create_event(request):
    """ creates a new RushEvent object """
    if request.method == 'POST':
        obj = RushEvent()
        obj.name = request.POST.get('name')
        obj.date = request.POST.get('date')
        obj.time = request.POST.get('time')
        obj.round = request.POST.get('round')
        obj.location = request.POST.get('location')
        if len(request.POST.getlist('new_rushees')) != 0:
            obj.new_rushees_allowed = True
        else:
            obj.new_rushees_allowed = False
        obj.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@staff_member_required
def remove_event(request, event_id):
    """ deletes a RushEvent object
        event_id -- primary key of event being deleted
    """
    RushEvent.objects.filter(id=event_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def current_rushees(request):
    """ page containing list of rushees who haven't been cut """
    template = loader.get_template('rush/current-rushees.html')
    rushees = Rushee.objects.filter(cut=0).order_by('name')
    context = {
        "rush_page": "active",
        "rushees": rushees,
        "settings": getSettings(),
    }
    return HttpResponse(template.render(context, request))

@login_required
# handles comment posting
def post_comment(request, rushee_id):
    """ creates a comment object attached to a rushee
        rushee_id -- primary key of rushee being commented on
    """
    form = CommentForm(request.POST)
    if form.is_valid():
        obj = Comment()
        obj.name = request.user.get_full_name()
        obj.body = form.cleaned_data['body']
        obj.rushee = Rushee.objects.get(id=rushee_id)
        obj.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponse("Comment not recorded.")


@staff_member_required
def remove_comment(request, comment_id):
    """ deletes a comment, removing it from the rushee's page
        comment_id -- primary key of comment being delete
    """
    comment = Comment.objects.get(id=comment_id)
    Comment.delete(comment)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# endorsements
@login_required
def endorse(request, rushee_id):
    """ adds a user to the rushee's list of endorsements and removes from opposition
        rushee_id -- primary key of rushee being endorsed
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    this_rushee.oppositions.remove(user)
    this_rushee.endorsements.add(user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# opposition
@login_required
def oppose(request, rushee_id):
    """ adds a user to the rushee's list of opposition and removes from endorsements
        rushee_id -- primary key of rushee being opposed
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    this_rushee.endorsements.remove(user)
    this_rushee.oppositions.add(user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def clear_endorsement(request, rushee_id):
    """ removes a user from both a rushee's endorsements and oppositions
        rushee_id -- primary key of rushee who's endorsements are being reset
                     for the requesting user
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    this_rushee.oppositions.remove(user)
    this_rushee.endorsements.remove(user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
