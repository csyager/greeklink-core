from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.index, name="index"),
    path('create_transaction', views.create_transaction, name="create_transaction"),
    path('transaction_details<int:transaction_id>', views.transaction_details, name="transaction_details"),
    path('submit_payment<int:transaction_id>', views.submit_payment, name="submit_payment"),
    path('submit_payment_with_transaction', views.submit_payment_with_transaction, name="submit_payment_with_transaction"),
    path('get_users_in_transaction', views.get_users_in_transaction, name="get_users_in_transaction"),
    path('get_users_in_transaction<int:transaction_id>', views.get_users_in_transaction, name="get_users_in_transaction")

]