from django.urls import path, include
from django.contrib import admin
from django.conf.urls import url, handler404, handler500
from django.conf import settings
from django.contrib.auth.views import LoginView
from core.forms import LoginForm
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # path('rushee<int:num>/', views.rushee, name="rushee"),
    # path('rushee<int:rushee_id>/comment', views.post_comment, name="comment"),
    # path('rushee<int:rushee_id>/push', views.push_rushee, name="push"),
    # path('rushee<int:rushee_id>/cut', views.cut_rushee, name="cut"),
    # path('votepage<int:rushee_id>', views.votepage, name="votepage"),
    # path('results<int:rushee_id>', views.results, name="results"),
    # path('vote<int:rushee_id>/<str:value>', views.vote, name="vote"),
    # path('voting/reset<int:rushee_id>', views.reset, name="reset"),
    # path('attendance<int:rushee_id>/<int:event_id>', views.attendance, name="attendance"),
    # path('remove_comment<int:comment_id>', views.remove_comment, name="remove_comment"),
    # path('endorse<int:rushee_id>', views.endorse, name="endorse"),
    # path('oppose<int:rushee_id>', views.oppose, name="oppose"),
    # path('clear_endorsement<int:rushee_id>', views.clear_endorsement, name="clear_endorsement"),
    path('current_rushees', views.current_rushees, name="current_rushees"),
    # path('events', views.events, name="events"),
    path('test', views.test, name="test")
]