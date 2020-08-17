from django import forms
from django.forms import ModelForm
from .models import ChapterEvent, RECURRENCE_CHOICES
import datetime
from django.core.validators import EMPTY_VALUES

class ChapterEventForm(ModelForm):
    name = forms.CharField(max_length=50, label='Name',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    date = forms.DateField(initial=datetime.date.today, label='Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded', 'placeholder': 'YYYY-mm-dd'}))
    time = forms.TimeField(label="Time",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control rounded', 'placeholder': "HH:mm:ss in 24 hour time"}))
    location = forms.CharField(max_length=50, label='Location',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    recurring = forms.ChoiceField(choices=RECURRENCE_CHOICES, label="Recurring",
        widget=forms.Select(attrs={'id': 'recurring_selection', 'class': 'form-control rounded'}))
    end_date = forms.DateField(label='End Date', required=False, initial=datetime.date.today,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded', 'placeholder': 'YYYY-mm-dd'}))

    def clean(self):
        recurring = self.cleaned_data.get('recurring')
        if recurring != 'None':
            end_date = self.cleaned_data.get('end_date')
            if end_date in EMPTY_VALUES:
                self._errors['end_date'] = self.error_class(['End date required'])
        return self.cleaned_data
    
    class Meta:
        model = ChapterEvent
        fields = ('name', 'date', 'time', 'location', 'recurring')
