""" views corresponding to rush/urls.py """

import re
import io
import base64
from django.core.files import File
from django.template import loader
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import Http404
from core.views import getSettings
from core.models import SiteSettings
from .forms import CommentForm, RusheeForm, FilterForm
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
    comments = Comment.objects.filter(rushee=obj)
    
    form = CommentForm()
    current_round = obj.round

    # for navigation buttons on rushee page
    next_url = ""
    prev_url = ""

    # check for filter in session variables
    try:
        # if show cut rushees filter is true, need to use list of all rushees
        if 'cut' in request.session['rushee_filter']:
            all_rushees = Rushee.objects.all()
        # otherwise, use list of only non-cut rushees
        else:
            all_rushees = Rushee.objects.filter(cut=False)
        # by default, next rushee should be next alphabetically in these lists
        next_rushee = all_rushees.filter(name__gt=obj.name).order_by('name')[0].id
        # loop through filters to further filter all_rushees
        for filter in request.session['rushee_filter']:
            if filter != 'cut':
                variable_column = filter
                search_type = 'icontains'
                filter_string = variable_column + '__' + search_type
                next_rushee = (all_rushees.filter(**{ filter_string: request.session['rushee_filter'][filter]})
                                .filter(name__gt=obj.name).order_by('name')[0].id)
            next_url = '/rush/rushee' + str(next_rushee)
    # filter found but this is last rushee alphabetically that filter applies to (rushees[0] DNE)
    except IndexError:
        next_url = ""

    # filter is not set in session, use default behavior
    except KeyError:
        # get next rushee alphabetically
        try:
            next_rushee = Rushee.objects.filter(name__gt=obj.name, cut=False).order_by('name')[0].id
            next_url = '/rush/rushee' + str(next_rushee)
        # this is last rushee alphabetically (rushees[0] DNE)
        except IndexError:
            next_url = ""

    # check for filter in session variables
    try:
        # if show cut rushees filter is set, need to use all rushees
        if 'cut' in request.session['rushee_filter']:
            all_rushees = Rushee.objects.all()
        # otherwise, use only non-cut rushees
        else:
            all_rushees = Rushee.objects.filter(cut=False)
        # default behavior, if no other filters just get next alphabetically 
        prev_rushee = all_rushees.filter(name__lt=obj.name).order_by('-name')[0].id
        # loop through filters to futher filter list
        for filter in request.session['rushee_filter']:
            if filter != 'cut':
                variable_column = filter
                search_type = 'icontains'
                filter_string = variable_column + '__' + search_type
                prev_rushee = (all_rushees.filter(**{ filter_string: request.session['rushee_filter'][filter]})
                                .filter(name__lt=obj.name).order_by('-name')[0].id)
            prev_url = '/rush/rushee' + str(prev_rushee)
    # filter found but this is first rushee alphabetically that filter applies to (rushees[0] DNE)
    except IndexError:
        prev_url = ""

    # filter is not set in session, use default behavior
    except KeyError:
        # get previous rushee alphabetically
        try:
            prev_rushee = Rushee.objects.filter(name__lt=obj.name, cut=False).order_by('-name')[0].id
            prev_url = '/rush/rushee' + str(prev_rushee)
        # this is first rushee alphabetically (rushee[0] DNE)
        except IndexError:
            prev_url = ""
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
            # immortalize this line for all time as the line that made our first
            # rush session take 7 hours instead of 4
            # obj.profile_picture_data = image_data
            obj.save()
            obj.profile_picture.save(str(obj.id) + '.png', File(img_io))
            obj.save()
        except (AttributeError, TypeError) as e:
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
    objects = Rushee.objects.filter(cut=False).order_by('name')
    all_events = RushEvent.objects.all().order_by('date')
    if int(event_id) != -1:
        this_event = RushEvent.objects.get(id=int(event_id))
        objects = (Rushee.objects.filter(round=this_event.round, cut=False)
                   .exclude(rushevent=this_event).order_by('name'))
    else:
        this_event = all_events.first()
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


@permission_required('rush.add_rushevent')
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
    else:
        raise Http404

@permission_required('rush.delete_rushevent')
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
    rushees = Rushee.objects.filter(cut=False).order_by('name')
    settings = getSettings()
    ROUND_CHOICES = [(0, "No filter")]
    num_rounds = settings.num_rush_rounds
    for i in range(1, num_rounds+1):
        ROUND_CHOICES.append((i, i))
    try:
        if request.session['rushee_filter']:
            if 'cut' in request.session['rushee_filter']:
                filter_form = FilterForm(initial=request.session['rushee_filter'])
                rushees = Rushee.objects.all().order_by('name')
            for filter in request.session['rushee_filter']:
                if filter != 'cut':
                    variable_column = filter
                    search_type = 'icontains'
                    filter_string = variable_column + '__' + search_type
                    rushees = rushees.filter(**{ filter_string: request.session['rushee_filter'][filter]})
                    filter_form = FilterForm(initial=request.session['rushee_filter'])
                    filter_form.fields['round'].choices = ROUND_CHOICES
    except KeyError:
        filter_form = FilterForm()
        filter_form.fields['round'].choices = ROUND_CHOICES
    context = {
        "rush_page": "active",
        "rushees": rushees,
        "filter_form": filter_form,
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


@permission_required('rush.delete_comment')
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

# stores a list of users who have already voted.  Is reset whenever voting is opened
# TODO: it would be really cool if there was an efficient way to have this persist so
#       even when voting is reopened only people who haven't voted yet get to vote
#       unless results are reset.  Problem is this requires the user to strictly follow
#       expected behavior, which they won't
# vote_list = []

@login_required
def vote(request, rushee_id, value):
    """ casts a vote for a rushee
        rushee_id -- primary key of rushee being voted on
        value -- what type of vote is being cast
            y -- yes vote
            n -- no vote
            a -- abstain vote
            b -- blackball vote
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    user = request.user
    if this_rushee.voting_open:
        if value == 'y':
            this_rushee.y += 1
            messages.info(request, ("Vote cast successfully!  You have voted yes on "
                                    + this_rushee.name), extra_tags="safe")
        if value == 'n':
            this_rushee.n += 1
            messages.info(request, ("Vote cast successfully!  You have voted "
                                    "no on " + this_rushee.name), extra_tags="safe")
        if value == 'a':
            this_rushee.a += 1
            messages.info(request, ("Vote cast successfully!  You have voted "
                                    "to abstain on " + this_rushee.name), extra_tags="safe")
        if value == 'b':
            this_rushee.b += 1
            this_rushee.blackball_list.add(user)
            messages.info(request, ("Vote cast successfully!  You have voted "
                                    "to blackball " + this_rushee.name), extra_tags="safe")
        this_rushee.save()
    else:
        messages.error(request, ("Vote was not cast, because voting is not open.  Voting must be "
                                 "opened by an admin before votes will be recorded."))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@permission_required('rush.change_rushee')
def push_rushee(request, rushee_id):
    """ push a rushee from the current voting round to the next one
        rushee_id -- primary key of rushee being pushed
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    this_rushee.y = 0
    this_rushee.n = 0
    this_rushee.a = 0
    this_rushee.b = 0
    current_round = this_rushee.round
    current_round += 1
    this_rushee.round = current_round
    this_rushee.save()

    # get next rushee
    try:
        next_rushee = (Rushee.objects.filter(name__gt=this_rushee.name, cut=False,
                                             round=current_round-1).order_by('name')[0].id)
        next_url = '/rush/rushee' + str(next_rushee)
    except IndexError:
        next_url = '/rush/current_rushees'

    return HttpResponseRedirect(next_url)


@permission_required('rush.change_rushee')
def cut_rushee(request, rushee_id):
    """ cut a rushee, setting cut equal to the round they were cut in
        rushee_id -- primary key of rushee being cut
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    this_rushee.y = 0
    this_rushee.n = 0
    this_rushee.a = 0
    this_rushee.b = 0
    current_round = this_rushee.round
    this_rushee.cut = True
    this_rushee.save()

    # get next rushee
    try:
        next_rushee = (Rushee.objects.filter(name__gt=this_rushee.name, cut=False, round=current_round)
                       .order_by('name')[0].id)
        next_url = '/rush/rushee' + str(next_rushee)
    except IndexError:
        next_url = '/rush/current_rushees'

    return HttpResponseRedirect(next_url)

@permission_required('rush.change_rushee')
def votepage(request, rushee_id):
    """ opens voting, displays a timer to show that voting is open, then redirects to results
        rushee_id -- primary key of rushee being voted on
    """
    # reset vote list
    this_rushee = Rushee.objects.get(id=rushee_id)
    this_rushee.voting_open = True
    this_rushee.save()
    # add additional data here if needed

    template = loader.get_template('rush/votepage.html')
    context = {
        "rushee": this_rushee,
        'settings': getSettings()
    }
    return HttpResponse(template.render(context, request))

@permission_required('rush.view_rushee')
def results(request, rushee_id):
    """ shows results of voting on a rushee
        rushee_id -- primary key of rushee whose results are being viewed
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    this_rushee.voting_open = False
    this_rushee.save()

    template = loader.get_template('rush/results.html')
    context = {
        "rushee": this_rushee,
        'settings': getSettings()
    }
    return HttpResponse(template.render(context, request))

@permission_required('rush.change_rushee')
def reset(request, rushee_id):
    """ resets votes cast on a rushee
        rushee_id -- primary key of rushee whose votes are being reset
    """
    this_rushee = Rushee.objects.get(id=rushee_id)
    this_rushee.y = 0
    this_rushee.n = 0
    this_rushee.a = 0
    this_rushee.b = 0
    this_rushee.blackball_list.clear()

    this_rushee.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def filter_rushees(request):
    """ filters the current rushees page and saves filter choices
        in session
    """

    if request.method == 'POST':
        form = FilterForm(request.POST)
        settings = getSettings()
        ROUND_CHOICES = [(0, "No filter")]
        num_rounds = settings.num_rush_rounds
        for i in range(1, num_rounds+1):
            ROUND_CHOICES.append((i, i))
        form.fields['round'].choices = ROUND_CHOICES
        if form.is_valid():
            filters = {}
            for field in form.fields:
                if form.cleaned_data[field] != '' and form.cleaned_data[field] != '0' and form.cleaned_data[field] != False:
                    filters[field] = form.cleaned_data[field]
            request.session['rushee_filter'] = filters
            # if session variable is empty, just delete it
            if not bool(request.session['rushee_filter']):
                del request.session['rushee_filter']
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponse(form.errors)
    else:
        raise Http404

@login_required
def clear_rushees_filter(request):
    """ clears the filter session variable """
    try:
        del request.session['rushee_filter']
    except KeyError:
        pass
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
