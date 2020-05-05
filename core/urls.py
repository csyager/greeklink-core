from django.urls import path, include
from django.contrib import admin
from django.conf.urls import url
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate, name='activate'),
    path('login/', LoginView.as_view(template_name='core/login.html'), name="login"),
    path('logout', views.brother_logout, name='logout'),
    path('resources', views.resources, name="resources"),
    path('search', views.SearchView.as_view(), name="search"),
    path('uploadfile', views.upload_file, name="upload_file"),
    path('addCal', views.addCal, name="addCal"),
    path('removeCal', views.removeCal, name="removeCal"),
    path('removeFile<int:file_id>', views.remove_file, name="remove_file"),
    path('social', views.social, name="social"),
    path('createSocialEvent', views.create_social_event, name="create_social_event"),
    path('social_event<int:event_id>', views.social_event, name="social_event"),
    path('removeSocialEvent<int:event_id>', views.remove_social_event, name="remove_social_event"),
    path('add_to_list<int:event_id>', views.add_to_list, name="add_to_list"),
    path('remove_from_list<int:event_id>/<int:attendee_id>', views.remove_from_list, name="remove_from_list"),
    path('clear_list<int:event_id>', views.clear_list, name="clear_list"),
    path('export_xls<int:event_id>', views.export_xls, name="export_xls"),
    path('removeLink<int:link_id>', views.remove_link, name="remove_link"),
    path('addLink', views.add_link, name="add_link"),
    path('add_announcement', views.add_announcement, name='add_announcement'),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)