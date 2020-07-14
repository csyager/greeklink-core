from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from core.views import getSettings
from core.models import OrgEvent
from calendar import HTMLCalendar
from datetime import datetime, timedelta

class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

def index(request):
    template = loader.get_template('cal/index.html')
    cal = Calendar()
    context = {
        'calendar': cal.formatmonth(2020, 7),
        'cal_page': 'active',
        'settings': getSettings()
    }
    return HttpResponse(template.render(context, request))