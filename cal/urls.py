  
""" URL paths for the rush application """

from django.urls import path
from . import views

app_name = 'cal'

urlpatterns = [
    path('', views.index, name="index"),
    path('create_chapter_event', views.create_chapter_event, name="create_chapter_event")
]