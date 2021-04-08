from django import forms
from core.models import SiteSettings
from .models import *
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.apps import apps


# form for leaving comments
class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['body']

    def save(self):
        comment = super(CommentForm, self).save(commit=False)
        comment.save()
        return comment


# form for initial rushee sign in
class RusheeForm(ModelForm):
    name = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Name'}))
    email = forms.EmailField(max_length=100, required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control rounded', 'placeholder': 'Email'}))
    year = forms.ChoiceField(choices=YEAR_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'form-control rounded'}))
    major = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Major'}))
    hometown = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Hometown'}))
    address = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'School Address'}))
    phone_number = forms.CharField(max_length=10, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Phone Number'}))

    in_person = forms.ChoiceField(choices={(True, 'Yes'), (False, 'No')}, label="Do you plan to participate in the in-person rush activities this year?", required=True,
        widget=forms.Select(attrs={'class': 'form-control rounded'}))

    friends_rushing = forms.CharField(max_length=100, label="Are you rushing with any friends or roommates?  This will be used to plan small group events.", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'List up to 3 names'}))

    class Meta:
        model = Rushee
        fields = ['name', 'email', 'year', 'major', 'hometown', 'address', 'phone_number', 'in_person', 'friends_rushing']

    def save(self):
        rushee = super(RusheeForm, self).save(commit=False)
        rushee.save()
        return rushee

year_choices = [
    (0, 'No filter'),
    (1, 'Freshman'),
    (2, 'Sophomore'),
    (3, 'Junior'),
    (4, 'Senior')
]

class FilterForm(forms.Form):
    name = forms.CharField(max_length=50, label='Name', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'No filter selected'}))
    round = forms.ChoiceField(label='Round Number', required=False,
        widget=forms.Select(attrs={'class': 'form-control rounded'}))
    major = forms.CharField(max_length=20, label='Major', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'No filter selected'}))
    year = forms.ChoiceField(label='Year', required=False, choices=year_choices,
        widget=forms.Select(attrs={'class': 'form-control rounded'}))
    hometown = forms.CharField(max_length=50, label='Hometown', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'No filter selected'}))
    cut = forms.BooleanField(label='Show cut rushees', required=False,
        widget=forms.CheckboxInput())
