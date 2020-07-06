from django import forms
from .models import *
from django.forms import ModelForm
from django.forms.widgets import TextInput
from core.views import getSettings

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
    name = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Name'}))
    email = forms.EmailField(max_length=100,
        widget=forms.EmailInput(attrs={'class': 'form-control rounded', 'placeholder': 'Email'}))
    year = forms.ChoiceField(choices=YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control rounded'}))
    major = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Major'}))
    hometown = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Hometown'}))
    address = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'School Address'}))
    phone_number = forms.CharField(max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Phone Number'}))

    class Meta:
        model = Rushee
        fields = ['name', 'email', 'year', 'major', 'hometown', 'address', 'phone_number']

    def save(self):
        rushee = super(RusheeForm, self).save(commit=False)
        rushee.save()
        return rushee

site_settings = getSettings()

ROUND_CHOICES = [(0, "No filter")]
for i in range(1, site_settings.num_rush_rounds+1):
    ROUND_CHOICES.append((i, i))


class FilterForm(forms.Form):
    name = forms.CharField(max_length=50, label='Name', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Name'}))
    round = forms.ChoiceField(choices=ROUND_CHOICES, label='Round Number',
        widget=forms.Select(attrs={'class': 'form-control rounded'}))
    major = forms.CharField(max_length=20, label='Major', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Major'}))
    hometown = forms.CharField(max_length=50, label='Hometown', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Hometown'}))