from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.template import loader, RequestContext

from core.views import getSettings

from.models import *

# Create your views here.

def test(request):
    template = loader.get_template('rush/test.html')
    context = {

    }
    return HttpResponse(template.render(context, request))

@login_required
def rushee(request, num):
    template = loader.get_template('deltasigrush/rushee.html')
    obj = Rushee.objects.get(id=num)
    events = Event.objects.all().order_by('date')
    try:
        comments = Comment.objects.filter(rushee=obj)
    except Comment.DoesNotExist:
        comments = None
    form = CommentForm()
    current_round = obj.round

     # get next rushee
    referer = request.META.get('HTTP_REFERER')
    path = parse.urlparse(referer).path
    if 'search' not in path and 'current-rushees' not in path:
        try:
            next_rushee = Rushee.objects.filter(id__gt = num, cut=0, round=current_round).order_by('id')[0].id
            next_url = '/rushee' + str(next_rushee)
            from_voting = True
        except Exception:
            from_voting = False
            next_url = ""
    else:
        from_voting = False
        next_url = ""

    context = {
        "rushee": obj,
        "comments": comments,
        "form": form,
        "events": events,
        'settings': getSettings(),
        'next_url': next_url,
        'from_voting': from_voting
    }
    return HttpResponse(template.render(context, request))


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
