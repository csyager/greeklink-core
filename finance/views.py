from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from core.views import getSettings
from django.contrib.auth.decorators import login_required, permission_required
from .forms import TransactionForm, TransactionDetailForm
from django.contrib import messages
from .models import Transaction, TransactionUserRelation
from django.contrib.auth.models import User

# Create your views here.

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

            