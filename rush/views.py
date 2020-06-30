""" views corresponding to rush/urls.py """

from urllib import parse
from django.template import loader
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from core.views import getSettings

from .forms import CommentForm
from .models import Rushee, RushEvent, Comment

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
    }
    return HttpResponse(template.render(context, request))


@login_required
def signin(request):
    return HttpResponse('Signin page')

@login_required
def events(request):
    return HttpResponse('Rush events page')

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

