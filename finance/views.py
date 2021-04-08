from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from core.views import getSettings
from django.contrib.auth.decorators import login_required, permission_required
from .forms import TransactionForm, TransactionDetailForm, RecordPaymentForm
from django.contrib import messages
from .models import Transaction, TransactionUserRelation
from django.contrib.auth.models import User
import matplotlib
import matplotlib.pyplot as plt
from mpld3 import fig_to_html, plugins, utils

# Create your views here.
matplotlib.use('agg')

@login_required
def index(request):
    '''
        index for finance page
    '''
    template = loader.get_template('finance/index.html')
    context = {
        'settings': getSettings(),
        'finance_page': 'active',
        'transaction_form': TransactionForm(),
        'transaction_detail_form': TransactionDetailForm()
    }
    return HttpResponse(template.render(context, request))


def create_transaction(request):
    '''
        creates a transaction object
    '''
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            print("valid form")
            name = form.cleaned_data.get('name')
            description = form.cleaned_data.get('description')
            due_date = form.cleaned_data.get('due_date')
            amount = form.cleaned_data.get('amount')
            groups = form.cleaned_data.get('groups')
            users = form.cleaned_data.get('users')
            transaction = Transaction.objects.create(name=name, description=description, due_date=due_date, amount=amount)
            print("transaction created")
            transaction.save()
            for user in users:
                u = User.objects.get(username=user)
                user_relation = TransactionUserRelation.objects.create(user=u, transaction=transaction)
                user_relation.save()
            for group in groups:
                for user in User.objects.filter(groups__name=group):
                    if not TransactionUserRelation.objects.get(user=user, transaction=transaction):
                        user_relation = TransactionUserRelation.objects.create(user=user, transaction=transaction)
                        user_relation.save()
            messages.success(request, "Transaction " + transaction.name + " has been successfully created.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            # errors = ""
            # for field in form:
            #     for error in field.errors:
            #         print(error)
            #         errors += error
            # for error in form.non_field_errors():
            #     print(error)
            #     errors += error
            messages.error(request, "Something went wrong.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        raise Http404


def transaction_details(request, transaction_id):
    '''
        shows details on a transaction
    '''
    transaction = Transaction.objects.get(id=transaction_id)
    transaction_user_relation = transaction.transaction_user_list

    num_requested = len(transaction_user_relation.all())
    total_collected = 0.00
    for elem in transaction_user_relation.all():
        total_collected += elem.amount_paid

    percentage = round(100*(total_collected/transaction.amount), 2)

    # pie chart
    labels = 'Paid', 'Outstanding'
    sizes = percentage, 100.0-percentage
    explode = (0, 0)
    fig1, ax1 = plt.subplots()
    wedges = ax1.pie(sizes, explode=explode, colors=['green', 'red'], labels=labels, autopct='%1.1f%%',
            shadow=False, startangle=0)
    ax1.axis('equal')
    graph_html = fig_to_html(fig1)

    template = loader.get_template('finance/transaction_details.html')
    context = {
        'settings': getSettings(),
        'finance_page': 'active',
        'transaction': transaction,
        'transaction_user_relation': transaction_user_relation,
        'num_requested': num_requested,
        'total_collected': float(total_collected),
        'total_requested': float(num_requested * transaction.amount),
        'percentage': float(percentage),
        'record_payment_form': RecordPaymentForm(transaction=transaction),
        'graph_html': graph_html
    }
    return HttpResponse(template.render(context, request))



def submit_payment(request, transaction_id):
    '''
        submit a payment
    '''
    transaction = Transaction.objects.get(id=transaction_id)
    user_id = int(request.POST.get('user'))
    user = User.objects.get(id=user_id)
    amount = float(request.POST.get('amount'))

    transaction_user_relation = TransactionUserRelation.objects.get(transaction=transaction, user=user)
    transaction_user_relation.amount_paid += amount
    transaction_user_relation.save()

    messages.success(request, user.username + "'s payment of $" + '%.2f' % amount + " for transaction " + transaction.name + " successfully recorded.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))