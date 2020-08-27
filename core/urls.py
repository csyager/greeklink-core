from django.urls import path, include
from django.contrib import admin
from django.conf.urls import url, handler404, handler500
from django.conf import settings
from django.contrib.auth.views import LoginView
from core.forms import LoginForm
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),   
    path('signup/', views.signup, name='signup'),
    path('resend_verification_email<int:user_id>', views.resend_verification_email, name='resend_verification_email'),
    path('activate/<int:user_id>/<str:token>', views.activate, name='activate'),
    path('forgot_credentials', views.forgot_credentials, name='forgot_credentials'),
    path('reset_password<int:user_id>/<str:token>', views.reset_password, name='reset_password'),
    path('login/', views.CustomLoginView.as_view(template_name='core/login.html', authentication_form=LoginForm), name="login"),
    path('logout', views.logout_user, name='logout'),
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
    path('check_attendee', views.check_attendee, name="check_attendee"),
    path('refresh_attendees', views.refresh_attendees, name="refresh_attendees"),
    path('toggle_party_mode<int:event_id>', views.toggle_party_mode, name='toggle_party_mode'),
    path('clear_list<int:event_id>', views.clear_list, name="clear_list"),
    path('export_xls<int:event_id>', views.export_xls, name="export_xls"),
    path('save_as_roster<int:event_id>', views.save_as_roster, name="save_as_roster"),
    path('create_roster', views.create_roster, name="create_roster"),
    path('roster<int:roster_id>', views.roster, name="roster"),
    path('edit_roster<int:roster_id>', views.edit_roster, name="edit_roster"),
    path('remove_from_roster<int:roster_id>/<int:member_id>', views.remove_from_roster, name="remove_from_roster"),
    path('add_roster_to_events<int:roster_id>', views.add_roster_to_events, name="add_roster_to_events"),
    path('remove_roster<int:roster_id>', views.remove_roster, name="remove_roster"),
    path('removeLink<int:link_id>', views.remove_link, name="remove_link"),
    path('addLink', views.add_link, name="add_link"),
    path('add_announcement', views.add_announcement, name='add_announcement'),
    path('all_announcements', views.all_announcements, name='all_announcements'),
    path('removeAnnouncement<int:announcement_id>', views.remove_announcement, name="remove_announcement"),
    path('editSocialEvent<int:event_id>', views.edit_social_event, name="edit_social_event"),
    path('support/', views.support_request, name='support'),
]


if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)