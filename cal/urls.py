  
""" URL paths for the cal application """

from django.urls import path
from . import views

app_name = 'cal'

urlpatterns = [
    path('', views.index, name="index"),
    path('date/<int:year>/<int:month>/<int:day>', views.date, name="date"),
    path('create_chapter_event', views.create_chapter_event, name="create_chapter_event"),
    path('delete_chapter_event<int:event_id>', views.delete_chapter_event, name='delete_chapter_event'),
    path('delete_chapter_event_recursive<int:event_id>', views.delete_chapter_event_recursive, name='delete_chapter_event_recursive'),
    path('edit_chapter_event<int:event_id>', views.edit_chapter_event, name='edit_chapter_event'),
]