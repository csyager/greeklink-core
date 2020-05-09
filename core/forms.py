from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.core.exceptions import ValidationError

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
                _("This account is inactive."),
                code='inactive',
            )
        

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

    class Meta:
        model = User
        fields = ('username', 'email', 'verification_key', 'first_name', 'last_name', 'password1', 'password2')


class UploadFileForm(ModelForm):
    name = forms.CharField(max_length=50)
    file = forms.FileField()
    description = forms.CharField(max_length=280, widget=forms.Textarea)

    class Meta:
        model = ResourceFile
        fields = ('name', 'file', 'description')


class LinkForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(LinkForm, self).__init__(*args, **kwargs)
        self.fields['url'].label = "URL"

    name = forms.CharField(max_length=50)
    url = forms.URLField()
    description = forms.CharField(max_length=280, widget=forms.Textarea)

    class Meta:
        model = ResourceLink
        fields = ('name', 'url', 'description')


class AnnouncementForm(ModelForm):
    title = forms.CharField(max_length=50)
    target = forms.URLField(required=False)
    body = forms.CharField(max_length=280, widget=forms.Textarea)

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