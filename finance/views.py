""" views controller for the finance module
"""

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from core.views import getSettings
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_POST
from .forms import (TransactionForm, TransactionDetailForm, 
                    RecordPaymentForm, RecordPaymentWithTransactionForm,
                    CreateBudgetLineItemForm)
from django.contrib import messages
from .models import Transaction, TransactionUserRelation, BudgetLineItem, PaymentEvent
from django.contrib.auth.models import User
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import StrMethodFormatter, FixedFormatter
import numpy as np
from mpld3 import fig_to_html, plugins, utils
from datetime import datetime, timedelta, date
import json
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
import xlwt

# Create your views here.
matplotlib.use('agg')

@login_required
def index(request):
    '''
        index for finance page
    '''
    template = loader.get_template('finance/index.html')

    last_7_days = []
    today = datetime.today()
    rounded_date = (today - timedelta(hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond))
    payment_events = PaymentEvent.objects.filter(date__range=[today.date()-timedelta(7), today.date()])
    y1=[]
    y2=[]
    for i in range(0, 7):
        this_date = rounded_date - timedelta(i)
        last_7_days.append(this_date)
        costs = 0
        profits = 0
        for e in payment_events.filter(date=this_date):
            if e.is_cost:
                costs += e.amount
            else:
                profits += e.amount
        y1.append(profits)
        y2.append(costs)
    
    x=last_7_days
    
    # pylint: disable=too-many-function-args
    plot = figure(title='Line Graph', x_axis_label='Date', y_axis_label='Amount', plot_width=300, plot_height=300, sizing_mode='scale_width', x_axis_type='datetime')
    plot.multi_line([x, x], [y1, y2], color=["green", "red"], line_width=2) 
    plot.line(x, y2, line_color="red", line_width=2, legend_label="Costs")
    plot.line(x, y1, line_color="green", line_width=2, legend_label="Profits")
    # pylint: enable=too-many-function-args
    
    plot.legend.location = "top_left"

    script, graph_html = components(plot)

    upcoming_budget_line_items = BudgetLineItem.objects.filter(due_date__gte=today, due_date__lte=today+timedelta(14), is_cost=True).order_by('due_date')

    context = {
        'settings': getSettings(),
        'finance_page': 'active',
        'transaction_form': TransactionForm(),
        'transaction_detail_form': TransactionDetailForm(),
        'record_payment_with_transaction_form': RecordPaymentWithTransactionForm(),
        'script': script,
        'graph_html': graph_html,
        'upcoming_budget_line_items': upcoming_budget_line_items
    }
    return HttpResponse(template.render(context, request))


def create_transaction(request):
    '''
        creates a transaction object
    '''
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            description = form.cleaned_data.get('description')
            due_date = form.cleaned_data.get('due_date')
            amount = form.cleaned_data.get('amount')
            groups = form.cleaned_data.get('groups')
            users = form.cleaned_data.get('users')
            create_line_item = request.POST.get('create_line_item')
            transaction = Transaction.objects.create(name=name, description=description, due_date=due_date, amount=amount)
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
            if create_line_item:
                line_item = BudgetLineItem.objects.create(transaction=transaction)
            
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
    fig1.set_figwidth(3.5)
    fig1.set_figheight(3.5)
    graph_html = fig_to_html(fig1, figid="transaction-pie-chart")

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

    payment_event = PaymentEvent.objects.create(description=f"Payment for transaction {transaction} by user {user}", amount=amount)
    payment_event.save()

    transaction_user_relation = TransactionUserRelation.objects.get(transaction=transaction, user=user)
    transaction_user_relation.amount_paid += amount
    transaction_user_relation.save()

    messages.success(request, user.username + "'s payment of $" + '%.2f' % amount + " for transaction " + transaction.name + " successfully recorded.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def submit_payment_with_transaction(request):
    '''
        submit a payment with the transaction id in the POST data
    '''
    transaction_id = int(request.POST.get('transaction'))
    transaction = Transaction.objects.get(id=transaction_id)
    user_id = int(request.POST.get('user'))
    user = User.objects.get(id=user_id)
    amount = float(request.POST.get('amount'))

    payment_event = PaymentEvent.objects.create(description=f"Payment for transaction {transaction} by user {user}", amount=amount)
    payment_event.save()

    transaction_user_relation = TransactionUserRelation.objects.get(transaction=transaction, user=user)
    transaction_user_relation.amount_paid += amount
    transaction_user_relation.save()

    messages.success(request, user.username + "'s payment of $" + '%.2f' % amount + " for transaction " + transaction.name + " successfully recorded.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def get_users_in_transaction(request, transaction_id=0):
    '''
        gets a list of users in a transaction
    '''
    if transaction_id == 0:
        return HttpResponse(json.dumps({}))

    transaction = Transaction.objects.get(id=transaction_id)
    ret_dict = {}
    for user in transaction.transaction_user_list.all():
        ret_dict[user.user.id] = user.user.username
    
    return HttpResponse(json.dumps(ret_dict))


def budget(request):
    '''
        direct user to the budget page, showing all budget line items
    '''

    template = loader.get_template('finance/budget.html')
    create_line_item_form = CreateBudgetLineItemForm()
    budget_line_items = BudgetLineItem.objects.all().order_by("due_date")
    balance = 0
    for elem in budget_line_items:
        if elem.is_cost:
            balance -= elem.amount
        else:
            balance += elem.amount
    context = {
        'settings': getSettings(),
        'finance_page': 'active',
        'create_line_item_form': create_line_item_form,
        'budget_line_items': budget_line_items,
        'balance': balance
    }
    return HttpResponse(template.render(context, request))


@require_POST
def create_budget_line_item(request):
    '''
        creates a line item for tracking payments and income in a budget
    '''
    form = CreateBudgetLineItemForm(request.POST)
    if form.is_valid():
        name = form.cleaned_data.get('name')
        description = form.cleaned_data.get('description')
        due_date = form.cleaned_data.get('due_date')
        amount = form.cleaned_data.get('amount')
        is_cost = form.cleaned_data.get('is_cost')
        line_item = BudgetLineItem.objects.create(name=name, description=description, due_date=due_date, amount=amount, is_cost=is_cost)
        line_item.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, "Something went wrong, and your budget line item could not be created.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def delete_budget_line_item(request, id):
    BudgetLineItem.objects.get(id=id).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def edit_budget_line_item(request, id):
    line_item = BudgetLineItem.objects.get(id=id)
    try:
        line_item.name = request.POST.get('name')
        line_item.description = request.POST.get('description')
        line_item.due_date = request.POST.get('due_date')
        line_item.amount = float(request.POST.get('amount'))
        line_item.is_cost = bool(request.POST.get('is_cost'))
        line_item.save()
        messages.success(request, f"{line_item.name} has been successfully updated!")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
        print(e)
        messages.error(request, "Something went wrong, and your budget line item could not be updated")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def clear_budget(request):
    BudgetLineItem.objects.all().delete()
    messages.success(request, "Budget successfully cleared!")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    