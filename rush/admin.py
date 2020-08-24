from django.contrib import admin
from .models import Rushee, RushEvent, Comment

# Register your models here.
admin.site.register(Rushee)
admin.site.register(RushEvent)
admin.site.register(Comment)