""" URL paths for the rush application """

from django.urls import path
from . import views

app_name = 'rush'

urlpatterns = [
    path('rushee<int:num>/', views.rushee, name="rushee"),
    path('signin', views.signin, name="signin"),
    path('signin<int:event_id>', views.signin, name='signin'),
    path('rushee<int:rushee_id>/comment', views.post_comment, name="comment"),
    path('register<int:event_id>', views.register, name='register'),
    # path('rushee<int:rushee_id>/push', views.push_rushee, name="push"),
    # path('rushee<int:rushee_id>/cut', views.cut_rushee, name="cut"),
    # path('votepage<int:rushee_id>', views.votepage, name="votepage"),
    # path('results<int:rushee_id>', views.results, name="results"),
    # path('vote<int:rushee_id>/<str:value>', views.vote, name="vote"),
    # path('voting/reset<int:rushee_id>', views.reset, name="reset"),
    path('attendance<int:rushee_id>/<int:event_id>', views.attendance, name="attendance"),
    path('remove_comment<int:comment_id>', views.remove_comment, name="remove_comment"),
    path('endorse<int:rushee_id>', views.endorse, name="endorse"),
    path('oppose<int:rushee_id>', views.oppose, name="oppose"),
    path('clear_endorsement<int:rushee_id>', views.clear_endorsement, name="clear_endorsement"),
    path('current_rushees', views.current_rushees, name="current_rushees"),
    path('events', views.events, name="events"),
    path('events/<int:event_id>', views.event, name="event"),
    path('createEvent', views.create_event, name="create_event"),
    path('removeEvent<int:event_id>', views.remove_event, name="remove_event"),
]
