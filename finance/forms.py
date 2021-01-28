from django import forms
from .models import *
from django.forms import ModelForm
from django.contrib.auth.models import User, Group
import datetime

class TransactionForm(forms.Form):
    name = forms.CharField(max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder':'Transaction Name'}))
    description = forms.CharField(max_length=500,
        widget=forms.Textarea(attrs={'class': 'form-control rounded', 'placeholder': 'Description', 'rows': '5'}))
    due_date = forms.DateField(initial=datetime.date.today,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded', 'placeholder': 'YYYY-mm-dd'}))
    amount = forms.DecimalField(max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control rounded', 'placeholder': 'Amount requested per person'}))
    groups = forms.MultipleChoiceField(choices=[], required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control rounded'}))
    users = forms.MultipleChoiceField(choices=[], required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control rounded'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        GROUPS = []
        for group in Group.objects.all():
            GROUPS.append((group.name, group.name))
        
        USERS = []
        for user in User.objects.all():
            USERS.append((user.username, user.username))
        
        self.fields['groups'].choices = GROUPS
        self.fields['users'].choices = USERS
        
    class Meta:
        model = Transaction
        fields = ('name', 'description', 'due_date', 'amount')


class TransactionDetailForm(forms.Form):
    transaction = forms.ChoiceField(choices=[], required=True,
        widget=forms.Select(attrs={'class': 'form-control rounded', 'id': 'transaction_details_select'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        OPTIONS = []
        for transaction in Transaction.objects.all():
            OPTIONS.append((transaction.id, transaction))

        self.fields['transaction'].choices = OPTIONS


class RecordPaymentForm(forms.Form):
    user = forms.ChoiceField(choices=[], required=True,
        widget=forms.Select(attrs={'class': 'form-control rounded', 'id': 'user_select'}))
    amount = forms.DecimalField(max_digits=6, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control rounded', 'placeholder': 'Amount paid'}))

    def __init__(self, *args, **kwargs):
        self.transaction = kwargs.pop('transaction')
        super().__init__(*args, **kwargs)
        USERS = []
        for user_relation in self.transaction.transaction_user_list.all():
            USERS.append((user_relation.user.id, user_relation.user.username))

        self.fields['user'].choices = USERS
