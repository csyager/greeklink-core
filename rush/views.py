""" views corresponding to rush/urls.py """

from urllib import parse
from django.template import loader
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from core.views import getSettings
import re, io

from .forms import CommentForm, RusheeForm
from .models import Rushee, RushEvent, Comment, RushEvent

# Create your views here.
@login_required
def rushee(request, num):
    """ rushee profile page """
    template = loader.get_template('rush/rushee.html')
    obj = Rushee.objects.get(id=num)
    events = RushEvent.objects.all().order_by('date')
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
            next_rushee = Rushee.objects.filter(name__gt = obj.name, cut = 0, round=current_round).order_by('name')[0].id
            next_url = '/rush/rushee' + str(next_rushee)
        except Exception:
            next_url = ""

        try:
            prev_rushee = Rushee.objects.filter(name__lt = obj.name, cut = 0, round=current_round).order_by('-name')[0].id 
            prev_url = '/rush/rushee' + str(prev_rushee)
        except Exception:
            prev_url = ""

    else:
        next_url = ""

    context = {
        "rushee": obj,
        "comments": comments,
        "form": form,
        "events": events,
        'settings': getSettings(),
        'next_url': next_url,
        'prev_url': prev_url,
        'rush_page': 'active'
    }
    return HttpResponse(template.render(context, request))


# adds a rushee to the database when they first sign in
@login_required
def register(request, event_id):
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
        dataUrlPattern = re.compile('data:image/png;base64,(.*)$')
        ImageData = request.POST.get('profile_picture_data')
        # try/catch: catches error thrown if picture data not inputted
        try:
            ImageData = dataUrlPattern.match(ImageData).group(1)
            ImageData = bytes(ImageData, 'UTF-8')
            ImageData = base64.b64decode(ImageData)
            img_io = io.BytesIO(ImageData)
            # obj.profile_picture_data = ImageData

            # obj.save()
            obj.profile_picture.save(str(obj.id) + '.png', File(img_io))
            obj.save()
        except AttributeError:
            obj.save()

        event = RushEvent.objects.get(id=event_id)
        event.attendance.add(obj)
        event.save()

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
    template = loader.get_template('rush/signin.html')
    form = RusheeForm()
    objects = Rushee.objects.filter(cut=0).order_by('name')
    events = RushEvent.objects.all().order_by('date')
    if int(event_id) != -1:
        event = RushEvent.objects.get(id=int(event_id))
        objects = Rushee.objects.filter(round=event.round, cut=0).exclude(rushevent=event).order_by('name')
    else:
        event = events.first()
    context = {
        "rush_page": "active",
        "form": form,
        "event": event,
        "objects": objects,
        "events": events,
        'settings': getSettings()
    }
    return HttpResponse(template.render(context, request))


# is submitted when a rushee signs into an event
@login_required
def attendance(request, rushee_id, event_id):
    template = loader.get_template('rush/register.html')
    obj = Rushee.objects.get(id=rushee_id)
    event = RushEvent.objects.get(id=event_id)
    event.attendance.add(obj)
    event.save()
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
    template = loader.get_template('rush/events.html')
    events = RushEvent.objects.all().order_by('date')
    settings = getSettings()
    round_range = range(1, settings.num_rush_rounds + 1)
    context = {
        'settings': settings,
        'round_range': round_range,
        'events': events,
        'rush_page': "active",
    }

    return HttpResponse(template.render(context, request))

@login_required
def event(request, event_id):
    event = RushEvent.objects.get(id=event_id)
    context = {
        'event': event,
        'settings': getSettings(),
        'rush_page': 'active',
    }
    template = loader.get_template('rush/event.html')
    return HttpResponse(template.render(context, request))


@staff_member_required
def create_event(request):
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
    RushEvent.objects.filter(id=event_id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def current_rushees(request):
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
    comment = Comment.objects.get(id=comment_id)
    Comment.delete(comment)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# endorsements
@login_required
def endorse(request, rushee_id):
    rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    rushee.oppositions.remove(user)
    rushee.endorsements.add(user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# opposition
@login_required
def oppose(request, rushee_id):
    rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    rushee.endorsements.remove(user)
    rushee.oppositions.add(user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def clear_endorsement(request, rushee_id):
    rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    rushee.oppositions.remove(user)
    rushee.endorsements.remove(user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

