from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.index, name="index"),
    path('create_transaction', views.create_transaction, name="create_transaction")
]