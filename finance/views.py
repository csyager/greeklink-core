from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from core.views import getSettings
from django.contrib.auth.decorators import login_required, permission_required

# Create your views here.

@login_required
def index(request):
    template = loader.get_template('finance/index.html')
    context = {
        'settings': getSettings(),
        'finance_page': 'active',
    }
    return HttpResponse(template.render(context, request))

