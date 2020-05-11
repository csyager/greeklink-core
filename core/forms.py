from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import *
from django.forms import ModelForm
from django.forms.widgets import TextInput

class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):

        username = forms.CharField(label='Username',
                                    max_length=100,
                                    widget=forms.TextInput(attrs={'class': 'form-control'}))
        password = forms.CharField(label='Password',
                                    max_length=100,
                                    widget=forms.PasswordInput(attrs={'class': 'form-control'}))
        class Meta(AuthenticationForm.Meta):
            fields = ('username', 'password')
        
        if not user.is_active:
            raise forms.ValidationError(
                _("This account is inactive."),
                code='inactive',
            )
        

class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    first_name = forms.CharField(max_length=30, help_text='Required')
    last_name = forms.CharField(max_length=30, help_text='Required')
    verification_key = forms.CharField(max_length=10, help_text='Required')

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