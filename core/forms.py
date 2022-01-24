from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import *
from django.forms import ModelForm, Select
from django.forms.widgets import TextInput
from django.core.exceptions import ValidationError
from organizations.models import Client, Community
import datetime

def getSettings():
    settings = SiteSettings.objects.all()
    if len(settings) == 0:
        newsettings = SiteSettings()
        newsettings.save()
        settings = SiteSettings.objects.all()
    settings = settings[0]
    return settings

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control rounded', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control rounded', 'placeholder': 'Password'}))

    class Meta:
        fields = ('username', 'password')
    
    def confirm_login_allowed(self, user):   
        if not user.is_active:
            raise forms.ValidationError(
                ("This account is inactive."),
                code='inactive',
            )

# disables first option in select to work like placeholder
class CustomSelect(Select):
    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        if not option.get('value'):
            option['attrs']['disabled'] = 'disabled'
        return option

class OrganizationSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(OrganizationSelectForm, self).__init__(*args, **kwargs)
        self.ORG_CHOICES = [('', 'Click to select organization')]
        for org in Client.objects.all().exclude(name='public').exclude(name='health'):
            self.ORG_CHOICES.append((org.domain_url, org.name))
        self.fields['organization'].choices = self.ORG_CHOICES

    organization = forms.ChoiceField(label="Select your organization",
        widget=CustomSelect(attrs={'placeholder': 'Select your organization', 'class': 'form-control rounded'}))

class SignupForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = "Password"
        self.fields['password2'].label = "Confirm Password"

    username=forms.CharField(max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Username'}))
    email = forms.EmailField(max_length=200, help_text='You will be asked to verify this email address in a moment.',
        widget=forms.EmailInput(attrs={'class': 'form-control rounded', 'placeholder': 'Email'}))
    first_name = forms.CharField(max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Last Name'}))
    verification_key = forms.CharField(max_length=10, help_text="This key should be provided by your site administrator",
        widget=forms.TextInput(attrs={'class': 'form-control rounded', 'placeholder': 'Verification Key'}))
    password1 = forms.CharField(max_length=30,
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded', 'placeholder': 'Password'}))
    password2 = forms.CharField(max_length=30,
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded', 'placeholder': 'Confirm Password'}))

    def clean_verification_key(self):
        settings = getSettings()
        verification_key = self.cleaned_data['verification_key']
        if verification_key != settings.verification_key:
            raise ValidationError("Verification key is incorrect")
        return verification_key

    def clean_email(self):
        email = self.cleaned_data['email']
        username = self.cleaned_data['username']
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise ValidationError("Email address is already in use.")
        return email

    class Meta:
        model = User
        fields = ('username', 'email', 'verification_key', 'first_name', 'last_name', 'password1', 'password2')


class ForgotCredentialsForm(forms.Form):
    email = forms.EmailField(max_length=100,
        widget=forms.EmailInput(attrs={'class': 'form-control rounded', 'placeholder': 'Email'}))

    class Meta:
        fields = ('email')

# pylint: disable=function-redefined
class SetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(self, *args, **kwargs)

    new_password1 = forms.CharField(max_length=100,
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(max_length=100,
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded', 'placeholder': 'Confirm New Password'}))
        
    class Meta:
        fields = ('new_password1', 'new_password2')


class UploadFileForm(ModelForm):
    name = forms.CharField(max_length=50, label='Name', 
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    file = forms.FileField(label="File",
        widget=forms.FileInput(attrs={'class': 'form-control-file rounded'}))
    description = forms.CharField(max_length=500, label='Description',
        widget=forms.Textarea(attrs={'class': 'form-control rounded', 'id': 'text_char_count'}))

    class Meta:
        model = ResourceFile
        fields = ('name', 'file', 'description')


class LinkForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(LinkForm, self).__init__(*args, **kwargs)
        self.fields['url'].label = "URL"

    name = forms.CharField(max_length=50, label="Name",
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    url = forms.URLField(label="URL",
        widget=forms.URLInput(attrs={'class': 'form-control rounded'}))
    description = forms.CharField(max_length=500, label="Description",
        widget=forms.Textarea(attrs={'class': 'form-control rounded', 'id': 'text_char_count_2'}))

    class Meta:
        model = ResourceLink
        fields = ('name', 'url', 'description')

class SocialEventForm(ModelForm):

    name = forms.CharField(max_length=50, label='Name',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    date = forms.DateField(initial=datetime.date.today, label='Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control rounded', 'placeholder': 'YYYY-mm-dd'}))
    time = forms.TimeField(label="Time",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control rounded', 'placeholder': "HH:mm:ss in 24 hour time"}))
    location = forms.CharField(max_length=50, label='Location',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    public = forms.BooleanField(label='Make event public?', required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    list_limit = forms.IntegerField(label='List Limit', required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control rounded', 'disabled': 'true', 'min': '1'}))

    class Meta:
        model = SocialEvent
        fields = ('name', 'date', 'time', 'location', 'is_public', 'list_limit')


class AnnouncementForm(ModelForm):
    title = forms.CharField(max_length=50, label='Title',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'}))
    target = forms.URLField(required=False, label='Target',
        widget=forms.URLInput(attrs={'class': 'form-control rounded'}))
    body = forms.CharField(max_length=500, label='Body',
        widget=forms.Textarea(attrs={'class': 'form-control rounded', 'id': 'text_char_count'}))
    send_emailBoolean = forms.BooleanField(required=False)

    class Meta:
        model = Announcement
        fields = ('title', 'target', 'body')

class SiteSettingsForm(ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'primary_color_theme': TextInput(attrs={'type': 'color'}),
        }

class SupportForm(forms.Form):
    from_email = forms.EmailField(required=True, label='Your email:',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'})) 
    subject = forms.CharField(required=True, label='Subject:',
        widget=forms.TextInput(attrs={'class': 'form-control rounded'})) 
    message = forms.CharField(required=True, max_length=500, label='Message:',
        widget=forms.Textarea(attrs={'class': 'form-control rounded', 'id': 'text_char_count'}))

class InviteUsersForm(forms.Form):
    recipients = forms.CharField(required=True, max_length=500, label="Recipients.  Separate each address by a newline.",
        widget=forms.Textarea(attrs={'class': 'form-control rounded', 'cols': '50', 'rows': '4'}))