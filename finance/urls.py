from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.index, name="index"),
    path('create_transaction', views.create_transaction, name="create_transaction"),
    path('transaction_details<int:transaction_id>', views.transaction_details, name="transaction_details"),
    path('submit_payment<int:transaction_id>', views.submit_payment, name="submit_payment")
]