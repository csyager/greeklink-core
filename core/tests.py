from django.test import TestCase, Client
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from .models import *
from django.urls import reverse
from . import views
from .forms import *
from datetime import date, timedelta
from django.utils import timezone
from .views import getSettings, handler500
from django.http import HttpResponse
from .tokens import *
import re
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from tenant_schemas.test.cases import TenantTestCase
from tenant_schemas.test.client import TenantClient


# Create your tests here.

# tests users signing in, out, and registering
class AuthenticationTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.u = User.objects.create(username="admin", is_superuser=True)
        self.client.force_login(self.u)

    # tests that logged in user can logout
    def test_logout_redirects_to_login(self):
        path = reverse('logout')
        response = self.client.post(path, follow=True)
        self.assertContains(response, 'Login')

    # gets template with signup form
    def test_signup_get_template(self):
        path = reverse('signup')
        response = self.client.get(path)
        self.assertContains(response, "Register")

    # tests that inactive users can activate with activate view
    def test_activate_view(self):
        user = User.objects.create(username="test", is_active="False")
        token = account_activation_token.make_token(user)
        path = reverse('activate', kwargs=dict(user_id=user.pk, token=token))
        response = self.client.post(path)
        self.assertContains(response, "Your account has been verified!")

    # tests user that does not exist
    def test_activate_user_does_not_exist(self):
        user = User.objects.create(username="test", is_active="False")
        token = account_activation_token.make_token(user)
        path = reverse('activate', kwargs=dict(user_id=user.pk, token=token))
        user.delete()
        response = self.client.post(path)
        self.assertContains(response, "Activation link is invalid")

    # tests invalid activation token
    def test_activate_user_invalid_token(self):
        user = User.objects.create(username="test", is_active="False")
        token = "999-99999999999999999999"
        path = reverse('activate', kwargs=dict(user_id=user.pk, token=token))
        response = self.client.post(path)
        self.assertContains(response, "Activation link is invalid")

    # tests logout
    def test_logout(self):
        user = User.objects.create(username="test")
        self.client.force_login(user)
        path = reverse('logout')
        response = self.client.post(path, follow=True)
        self.assertContains(response, "Login")


class SignupTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.form_data = {
            'username': 'test',
            'email': 'test@test.com',
            'first_name': 'Test_first',
            'last_name': 'Test_last',
            'verification_key': '9999',
            'password1': 'c0mpl#x_p@$$w0rd',
            'password2': 'c0mpl#x_p@$$w0rd'
        }

    # tests that signup form accepts valid input
    def test_signup_form(self):
        form = SignupForm(self.form_data)
        self.assertTrue(form.is_valid())

    # tests that form rejects passwords that are too simple
    def test_simple_password(self):
        self.form_data.update({
            'password1': 'password',
            'password2': 'password'
        })
        form = SignupForm(self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('This password is too common', form.errors['password2'][0])

    # tests that form rejects passwords that don't match
    def test_passwords_not_match(self):
        self.form_data.update({
            'password1': 'password1',
            'password2': 'password2'
        })
        form = SignupForm(self.form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual("The two password fields didn't match.", form.errors['password2'][0])

    # tests that form rejects usernames that are already in use
    def test_username_already_taken(self):
        User.objects.create(username="test")
        form = SignupForm(self.form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual("A user with that username already exists.", form.errors['username'][0])

    # tests that the user is redirected to successful verification page
    def test_valid_input_template(self):
        post_data = self.form_data
        path = reverse('signup')
        response = self.client.post(path, post_data)
        self.assertContains(response, "Thank you for signing up for GreekRho")

    # tests that inactive users can activate with activate view
    def test_activate_view(self):
        user = User.objects.create(username="test", is_active="False")
        token = account_activation_token.make_token(user)
        path = reverse('activate', kwargs=dict(user_id=user.pk, token=token))
        response = self.client.post(path)
        self.assertContains(response, "Your account has been verified!")

    # tests user that does not exist
    def test_activate_user_does_not_exist(self):
        user = User.objects.create(username="test", is_active="False")
        token = account_activation_token.make_token(user)
        path = reverse('activate', kwargs=dict(user_id=user.pk, token=token))
        user.delete()
        response = self.client.post(path)
        self.assertContains(response, "Activation link is invalid")

    # tests invalid activation token
    def test_activate_user_invalid_token(self):
        user = User.objects.create(username="test", is_active="False")
        token = "999-99999999999999999999"
        path = reverse('activate', kwargs=dict(user_id=user.pk, token=token))
        response = self.client.post(path)
        self.assertContains(response, "Activation link is invalid")

    # tests logout
    def test_logout(self):
        user = User.objects.create(username="test")
        self.client.force_login(user)
        path = reverse('logout')
        response = self.client.post(path, follow=True)
        self.assertContains(response, "Login")

    # tests forgot_credentials view under a get method
    def test_forgot_credentials_get(self):
        path = reverse('forgot_credentials')
        response = self.client.get(path)
        self.assertContains(response, "Forgot Credentials?")

    # tests forgot_credentials view under a post method
    def test_forgot_credentials_post(self):
        user = User.objects.create(username="test", email="test@test.com")
        post_data = {'email': 'test@test.com'}
        path = reverse('forgot_credentials')
        response = self.client.post(path, post_data, HTTP_REFERER=path, follow=True)    
        self.assertContains(response, "Email with password reset link has been sent.")

    # tests forgot_credentials view when email is not unique
    def test_forgot_credentials_common_email(self):
        user1 = User.objects.create(username="test1", email="test@test.com")
        user2 = User.objects.create(username="test2", email="test@test.com")
        post_data = {'email': 'test@test.com'}
        path = reverse('forgot_credentials')
        response = self.client.post(path, post_data, HTTP_REFERER=path, follow=True)
        self.assertContains(response, "Multiple accounts exist with the same email address.")

    # tests forgot_credentials view when email does not exist
    def test_forgot_credentials_email_dne(self):
        post_data = {'email': 'test@test.com'}
        path = reverse('forgot_credentials')
        response = self.client.post(path, post_data, HTTP_REFERER=path, follow=True)
        self.assertContains(response, "User with this email does not exist")

    # tests reset_password view under a get method
    def test_reset_password_view_get(self):
        user = User.objects.create(username="test", email="test@test.com")
        token = account_activation_token.make_token(user)
        path = reverse('reset_password', kwargs=dict(user_id=user.pk, token=token))
        response = self.client.get(path)
        self.assertContains(response, "Reset Password")

    # tests reset_password view under a post method
    def test_reset_password_view_post(self):
        user = User.objects.create(username="test", email="test@test.com")
        user.set_password("originalpassword")
        user.save()
        token = account_activation_token.make_token(user)
        path = reverse('reset_password', kwargs=dict(user_id=user.pk, token=token))
        post_data = {'new_password1': 'testpassword', 'new_password2': 'testpassword'}
        response = self.client.post(path, post_data)
        user.refresh_from_db()
        self.assertContains(response, "Your password has been changed.")
        self.assertFalse(user.check_password("originalpassword"))
        self.assertTrue(user.check_password("testpassword"))

    # tests reset password with invalid token
    def test_reset_password_invalid_token(self):
        user = User.objects.create(username="test", email="test@test.com")
        token = '999-99999999999999999999'
        path = reverse('reset_password', kwargs=dict(user_id=user.pk, token=token))
        response = self.client.get(path)
        self.assertContains(response, "Invalid token!")

    # tests reset password with passwords that don't match
    def test_reset_password_no_match(self):
        user = User.objects.create(username="test", email="test@test.com")
        user.set_password("originalpassword")
        user.save()
        token = account_activation_token.make_token(user)
        path = reverse('reset_password', kwargs=dict(user_id=user.pk, token=token))
        post_data = {'new_password1': 'testpassword1', 'new_password2': 'testpassword2'}
        response = self.client.post(path, post_data, HTTP_REFERER=path, follow=True)
        user.refresh_from_db()
        self.assertContains(response, "The two password fields")
        self.assertFalse(user.check_password('testpassword1'))
        self.assertFalse(user.check_password('testpassword2'))
        self.assertTrue(user.check_password("originalpassword"))

    def test_reset_password_common(self):
        user = User.objects.create(username="test", email="test@test.com")
        user.set_password("originalpassword")
        user.save()
        token = account_activation_token.make_token(user)
        path = reverse('reset_password', kwargs=dict(user_id=user.pk, token=token))
        post_data = {'new_password1': 'password', 'new_password2': 'password'}
        response = self.client.post(path, post_data, HTTP_REFERER=path, follow=True)
        user.refresh_from_db()
        self.assertContains(response, "This password is too common")
        self.assertFalse(user.check_password('password'))
        self.assertTrue(user.check_password('originalpassword'))

    def test_reset_password_short(self):
        user = User.objects.create(username="test", email="test@test.com")
        user.set_password("originalpassword")
        user.save()
        token = account_activation_token.make_token(user)
        path = reverse('reset_password', kwargs=dict(user_id=user.pk, token=token))
        post_data = {'new_password1': 'xyzabc', 'new_password2': 'xyzabc'}
        response = self.client.post(path, post_data, HTTP_REFERER=path, follow=True)
        user.refresh_from_db()
        self.assertContains(response, "This password is too short.")
        self.assertFalse(user.check_password('xyzabc'))
        self.assertTrue(user.check_password('originalpassword'))

class ResourcesAdminTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.admin = User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.client.force_login(self.admin)

    # tests that all admin options appear on the resources page
    def test_admin_controls(self):
        settings = getSettings()
        settings.calendar_embed = 'cal_link_here'
        settings.save()
        path = reverse('resources')
        response = self.client.post(path)
        self.assertContains(response, "Upload File")
        self.assertContains(response, "Add Link")
        self.assertContains(response, "modal")
    
    # tests resource file upload form
    def test_file_upload(self):
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'description': 'file description'}
        file_dict = {'file': file}
        form = UploadFileForm(post_dict, file_dict)
        self.assertTrue(form.is_valid())

    # tests resource file upload function
    def test_file_upload_view(self):
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'file': file, 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict, follow=True)
        self.assertContains(response, 'filename')

        # cleanup:  need to delete the file or it stays forever
        ResourceFile.objects.get(pk=1).file.delete()

    # tests error messages in file upload form
    def test_file_upload_errors(self):
        post_dict = {'name': 'filename', 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict)
        self.assertContains(response, b'file')

    # tests remove file function
    def test_remove_file(self):
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'file': file, 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict, follow=True)
        self.assertContains(response, 'filename')
        file_object = ResourceFile.objects.get(name='filename')
        path = reverse('remove_file', kwargs=dict(file_id=file_object.pk))
        response = self.client.post(path, follow=True)
        self.assertContains(response, 'filename', count=1)

    # tests the add calendar function
    def test_add_calendar(self):
        path = reverse('addCal')
        post_dict = {'cal_embed_link': 'hyperlink'}
        response = self.client.post(path, post_dict, follow=True)
        settings = getSettings()
        self.assertEqual(settings.calendar_embed, 'hyperlink')

    # tests the remove calendar function
    def test_remove_calendar(self):
        settings = getSettings()
        settings.calendar_embed = 'hyperlink'
        settings.save()
        path = reverse('removeCal')
        response = self.client.post(path)
        settings.refresh_from_db()
        self.assertEqual(settings.calendar_embed, '')

    # tests the add_link views.py function
    def test_add_link_view(self):
        post_dict = {'name': 'test', 'description': 'test description', 'url': 'https://www.google.com'}
        path = reverse('add_link')
        referer = reverse('resources')
        response = self.client.post(path, post_dict, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, '<a href="https://www.google.com"')
        
    # tests the link form
    def test_add_link_form_valid(self):
        form_data = {'name': 'test', 'description': 'test description', 'url': 'https://www.google.com'}
        form = LinkForm(data=form_data)
        self.assertTrue(form.is_valid)

    # tests when the link form is invalid
    def test_add_link_form_invalid(self):
        form_data = {}
        form = LinkForm(data=form_data)
        self.assertFalse(form.is_valid())

    # tests that errors are returned when link form is invalid
    def test_add_link_form_errors(self):
        post_dict = {}
        path = reverse('add_link')
        response = self.client.post(path, post_dict)
        self.assertContains(response, 'nameurldescription')

    # tests remove link function
    def test_remove_link(self):
        ResourceLink.objects.create(name='test', description='test description', url='https://www.google.com')
        link_object = ResourceLink.objects.get(name='test')
        path = reverse('remove_link', kwargs=dict(link_id=link_object.pk))
        referer = reverse('resources')
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(ResourceLink.objects.all())
        self.assertFalse(re.findall("<h4.*test</h4", str(response.content)))


class ResourcesTestCaseRegular(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.regular = User.objects.create(username="regular")
        self.client.force_login(self.regular)
        self.path = reverse('resources')
        self.response = self.client.post(self.path)
        
    # tests that resources page exists with proper header
    def test_resources_page_exists(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "Resources")  

    # tests that admin options do not appear for users without admin privileges
    def test_regular_users(self):
        self.assertNotContains(self.response, "No Google Calendar loaded!")
        self.assertNotContains(self.response, "Upload File")
        self.assertNotContains(self.response, "Add link")
        self.assertNotContains(self.response, "modal")

        
class AnnouncementsTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        u = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.client.force_login(u)
        a = Announcement.objects.create(user=u)

    # tests that announcement is displayed on index
    def test_announcement_appears(self):
        path = reverse('index')
        response = self.client.post(path)
        self.assertContains(response, '<li class="list-group-item">')

    # tests that add announcement button appears
    def test_add_announcement_button_appears(self):
        path = reverse('index')
        response = self.client.post(path)
        self.assertContains(response, "Add Announcement")

    # tests that announcement form takes valid input
    def test_add_announcement_form(self):
        form_data = {"title": "form test", "body": "test body"}
        form = AnnouncementForm(data=form_data)
        self.assertTrue(form.is_valid())

    # tests that announcement form doesn't take invalid input
    def test_add_announcement_form_invalid(self):
        form_data = {}
        form = AnnouncementForm(data=form_data)
        self.assertFalse(form.is_valid())

    # tests announcement form view
    def test_add_announcement_view(self):
        path = reverse('add_announcement')
        referer = reverse('index')
        post_dict = {'title': 'test', 'target': 'https://www.google.com', 'body': 'announcement body'}
        response = self.client.post(path, post_dict, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "announcement body")

    # tests announcement form view with invalid input
    def test_add_announcement_view_invalid(self):
        path = reverse('add_announcement')
        post_dict = {}
        referer = reverse('index')
        response = self.client.post(path, post_dict, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, 'Announcement was not successfully posted, because of the following errors:  This field is required.  This field is required.')


class SocialTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.admin = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.client.force_login(self.admin)
        self.event = SocialEvent.objects.create()
        
    # tests that the social page exists with the proper header
    def test_social_home_template(self):
        path = reverse('social')
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Social</h1>")

    # tests that events in the database appear on the social page
    def test_event_on_home_page(self):
        path = reverse('social')
        response = self.client.post(path)
        self.assertContains(response, '<a href="social_event' + str(self.event.pk))
    
    # tests the create event function
    def test_create_event(self):
        path = reverse('create_social_event')
        form_data = {'name': 'test_name', 'date': '2001-01-01', 'time': '12:00', 'location': "test_location"}
        form = SocialEventForm(form_data)
        self.assertTrue(form.is_valid)
        response = self.client.post(path, form_data, HTTP_REFERER=reverse('social'), follow=True)
        self.assertContains(response, 'test_name -- Jan. 1, 2001, noon')

    # tests that the page for an individual social event exists
    def test_social_event_page_exists(self):
        path = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
    
    # tests that the social event page populates with relevant data
    def test_social_event_page_populates(self):
        path = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path)
        content = str(response.content)
        self.assertTrue(re.findall('<h1.*test</h1>', content))
        self.assertContains(response, "Jan. 1, 2000, noon")

    # tests the remove_social_event function
    def test_remove_social_event(self):
        path = reverse('remove_social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, HTTP_REFERER=reverse('social'), follow=True)
        self.assertNotContains(response, "test_name -- Jan. 1, 2001, noon")
        self.assertRaises(SocialEvent.DoesNotExist, SocialEvent.objects.get, id=1)

    # tests that the add_to_list function works with both individual and multiple input
    def test_add_to_list_individual_and_multiple(self):
        path = reverse('add_to_list', kwargs=dict(event_id=self.event.pk))
        post_data = {'multiple_names': 'many_name1\nmany_name2\nmany_name3', 'name': 'individual_name'}
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer)
        self.assertTrue(Attendee.objects.filter(name="many_name1"))
        self.assertTrue(Attendee.objects.filter(name="many_name2"))
        self.assertTrue(Attendee.objects.filter(name="many_name3"))
        self.assertTrue(Attendee.objects.filter(name="individual_name"))

    # tests that add_to_list function works with only individual input
    def test_add_to_list_individual(self):
        path = reverse('add_to_list', kwargs=dict(event_id=self.event.pk))
        post_data = {'multiple_names': '', 'name': 'individual_name'}
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer)
        self.assertTrue(Attendee.objects.filter(name="individual_name"))
        self.assertFalse(Attendee.objects.filter(name="many_name"))

    # tests that add_to_list function works with only multiple-name input
    def test_add_to_list_multiple(self):
        path = reverse('add_to_list', kwargs=dict(event_id=self.event.pk))
        post_data = {'multiple_names': 'many_name1\nmany_name2\nmany_name3', 'name': ''}
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer)
        self.assertTrue(Attendee.objects.filter(name="many_name1"))
        self.assertTrue(Attendee.objects.filter(name="many_name2"))
        self.assertTrue(Attendee.objects.filter(name="many_name3"))
        self.assertFalse(Attendee.objects.filter(name="individual_name"))

class SocialEventTestCase(TenantTestCase):
    
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.admin = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.client.force_login(self.admin)
        self.event = SocialEvent.objects.create()
        self.attendees = []
        for i in range(1, 4):
             a = Attendee.objects.create(name="attendee" + str(i), user=self.admin, event=self.event)
             self.attendees.append(a)
        self.event.save()

    # tests remove_from_list feature to make sure attendees are removed from database and UI
    def test_remove_from_list(self):
        path = reverse('remove_from_list', kwargs=dict(event_id=self.event.pk, attendee_id=self.attendees[0].pk))
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(Attendee.objects.filter(name="attendee1"))
        self.assertFalse(re.findall("<td.*>attendee1</td>", str(response.content)))
        self.assertTrue(re.findall("<td.*>attendee2</td>", str(response.content)))
        path = reverse('remove_from_list', kwargs=dict(event_id=self.event.pk, attendee_id=self.attendees[1].pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(Attendee.objects.filter(name="attendee2"))
        self.assertFalse(re.findall("<td.*>attendee2</td>", str(response.content)))
        self.assertTrue(re.findall("<td.*>attendee3</td>", str(response.content)))

    # tests clear list feature
    def test_clear_list(self):
        path = reverse('clear_list', kwargs=dict(event_id=self.event.pk))
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        content = str(response.content)
        self.assertFalse(re.findall("<td>attendee[1-3]</td>", content))
        self.assertFalse(self.event.list.all())

    # tests exporting a spreadsheet of attendees
    def test_export_xls(self):
        path = reverse('export_xls', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path)
        self.assertEqual(response.get('Content-Type'), 'application/ms-excel')
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename=' + str(self.event.pk) + '_attendance.xls')

    # tests adding single duplicate name to the list
    def test_add_individual_duplicate(self):
        path = reverse('add_to_list', kwargs=dict(event_id=self.event.pk))
        # should fail, because name is a duplicate
        post_data = {'multiple_names': '', 'name': 'attendee1'}
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, " <b>The following name was not added to the list, because it is a duplicate:</b> attendee1")
        self.assertEqual(len(Attendee.objects.filter(name="attendee1")), 1)

    # tests adding multiple duplicate names to the list
    def test_add_multiple_duplicate(self):
        path = reverse('add_to_list', kwargs=dict(event_id=self.event.pk))
        # should fail, because both names are duplicates
        post_data = {'multiple_names': 'attendee1\nattendee2', 'name': ''}
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, " <b>The following name was not added to the list, because it is a duplicate:</b> attendee1")
        self.assertContains(response, " <b>The following name was not added to the list, because it is a duplicate:</b> attendee2")
        self.assertEqual(len(Attendee.objects.filter(name="attendee1")), 1)
        self.assertEqual(len(Attendee.objects.filter(name="attendee2")), 1)
    
    # tests adding multiple names where some are duplicates and some aren't
    def test_add_duplicates_and_new(self):
        path = reverse('add_to_list', kwargs=dict(event_id=self.event.pk))
        # one should fail, one should work
        post_data = {'multiple_names': 'attendee1\nattendee5', 'name': ''}
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "<b>The following name was not added to the list, because it is a duplicate:</b> attendee1")
        self.assertNotContains(response, "<b>The following name was not added to the list, because it is a duplicate:</b> attendee2")
        self.assertEqual(len(Attendee.objects.filter(name="attendee1")), 1)
        self.assertEqual(len(Attendee.objects.filter(name="attendee2")), 1)

    # tests checking attendance feature
    def test_check_attendance(self):
        path = reverse('check_attendee')
        a = self.event.list.first()
        get_data = {'attendee_id': a.id}
        response = self.client.get(path, get_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'attended': True}
        )
        a.refresh_from_db()
        self.assertTrue(a.attended)

    def test_uncheck_attendance(self):
        a = self.event.list.first()
        a.attended = True
        a.save()
        path = reverse('check_attendee')
        get_data = {'attendee_id': a.id}
        response = self.client.get(path, get_data)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'attended': False}
        )
        a.refresh_from_db()
        self.assertFalse(a.attended)

    # tests refresh_attendees view for three attendees with attended=False
    def test_refresh_attendees_static(self):
        path = reverse('refresh_attendees')
        get_data = {'event_id': self.event.id}
        response = self.client.get(path, get_data)
        self.assertEqual(response.status_code, 200)
        # response should be false for all three attendees
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                str(self.attendees[0].pk): False,
                str(self.attendees[1].pk): False,
                str(self.attendees[2].pk): False
            }
        )
    
    # tests refresh_attendees view when status of attendee changes, to ensure change is propagated
    def test_refresh_attendees_dynamic(self):
        path = reverse('refresh_attendees')
        get_data = {'event_id': self.event.id}
        response = self.client.get(path, get_data)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                str(self.attendees[0].pk): False,
                str(self.attendees[1].pk): False,
                str(self.attendees[2].pk): False
            }
        )

        # change one of the attendees, to see if the refresh changes the JSON response
        a = Attendee.objects.get(id=self.attendees[1].pk)
        a.attended = True
        a.save()

        response = self.client.get(path, get_data)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                str(self.attendees[0].pk): False,
                str(self.attendees[1].pk): True,
                str(self.attendees[2].pk): False
            }
        )

    # test toggle_party_mode view
    def test_toggle_party_mode_view(self):
        # event.party_mode is initially false, request should make it true
        path = reverse('toggle_party_mode', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path)
        self.event.refresh_from_db()
        self.assertTrue(self.event.party_mode)

        # sending request again should make event.party_mode false again
        response = self.client.post(path)
        self.event.refresh_from_db()
        self.assertFalse(self.event.party_mode)

    # test toggle_party_mode template
    def test_toggle_party_mode_template(self):
        # party mode should initially be false
        referer = reverse('social_event', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(referer)

        # when party mode is off, the label by the button should say off
        self.assertContains(response, "Party mode off")
        # the add to list form should be availiable
        self.assertContains(response, "Type Full Name Here")
        # the ajax script refreshing the list should not be linked
        self.assertFalse(re.findall('<script src=".*cross_off_list.js', str(response.content)))
        # the "attended" column of the list table should not be present
        self.assertNotContains(response, "Attended")

        # set party mode to true
        path = reverse('toggle_party_mode', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        
        # when party mode is on, the label by the button should say on
        self.assertContains(response, "Party mode on")
        # The attended column should be present
        self.assertContains(response, "Attended")
        # the ajax script refreshing the list should be linked
        self.assertTrue(re.findall('<script src=".*cross_off_list.js', str(response.content)))
        # the add to list form should not be available
        self.assertNotContains(response, "Type Full Name Here")
        

class ErrorsTestCase(TenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)
    
    # tests custom 404 page appears on 404 error
    def test_404_custom_page(self):
        path = '/path/that/does/not/exist'
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
        self.assertIn("The requested URL, " + path + " could not be found.", str(response.content))

class SearchTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.admin = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.client.force_login(self.admin)
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        for i in range(0, 10):
            SocialEvent.objects.create(name="test_event_" + str(i))
            ResourceLink.objects.create(name="test_link_" + str(i), description="test", url="https://www.google.com")
            Announcement.objects.create(title="announcement_" + str(i))
            ResourceFile.objects.create(name="test_file_" + str(i), file=file, description="test")

    # deletes any files created in this test case from the server
    def tearDown(self):
        for i in range(0, 10):
            ResourceFile.objects.get(name="test_file_" + str(i)).file.delete()

    # tests basic search
    def test_search_basic(self):
        path = reverse('search')
        get_data = {'query': 'test'}
        response = self.client.get(path, get_data, follow=True)
        self.assertContains(response, "40 results")

    # test paginate feature for more than 10 results
    def test_search_paginate_more_than_10(self):
        path = reverse('search')
        get_data = {'query': 'test'}
        response = self.client.get(path, get_data, follow=True)
        # should be 40 results over 4 pages
        self.assertContains(response, 'nav aria-label="Page navigation"')
        self.assertContains(response, 'href="search?query=test&page=4')
        self.assertNotContains(response, 'href="search?query=test&page=5')
    
    # test paginate doesn't appear with fewer than 10
    def test_search_paginate_fewer_than_10(self):
        path = reverse('search')
        get_data = {'query': 'test1'}
        response = self.client.get(path, get_data, follow=True)
        self.assertNotContains(response, 'nav aria-label="Page navigation"')

    # test search with empty string query
    def test_search_empty_string(self):
        path = reverse('search')
        get_data = {'query': ''}
        response = self.client.get(path, get_data, follow=True)
        self.assertContains(response, '0 results for <b>None</b>')


class RosterTestCase(TenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.admin = User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.client.force_login(self.admin)
        self.roster = Roster.objects.create(title="test_roster")
    
    # tests roster view function
    def test_roster_view(self):
        path = reverse('roster', kwargs=dict(roster_id=self.roster.pk))
        response = self.client.get(path)
        self.assertContains(response, "test_roster</h1>")

    # tests roster appears in social view
    def test_roster_appears_in_social(self):
        path = reverse('social')
        response = self.client.get(path)
        self.assertContains(response, "test_roster</a>")
    
    # tests edit_roster view function
    def test_edit_roster_view(self):
        path = reverse('edit_roster', kwargs=dict(roster_id=self.roster.pk))
        referer = reverse('roster', kwargs=dict(roster_id=self.roster.pk))
        post_data = {
            'updated_members': 'test1\ntest2\ntest3'
        }
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "test1</td>")
        self.assertContains(response, "test2</td>")
        self.assertContains(response, "test3</td>")
        self.assertEqual(self.roster.members.count(), 3)

    # tests editing roster with duplicates
    def test_edit_roster_duplicates(self):
        path = reverse('edit_roster', kwargs=dict(roster_id=self.roster.pk))
        referer = reverse('roster', kwargs=dict(roster_id=self.roster.pk))
        # contains duplicate of test1
        post_data = {
            'updated_members': 'test1\ntest2\ntest1'
        }
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "The following name was not added to the roster, because it is a duplicate:</b> test1")
        self.assertEqual(self.roster.members.count(), 2)

    # tests edit roster with get request, should return 404
    def test_edit_roster_get(self):
        path = reverse('edit_roster', kwargs=dict(roster_id=1))
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
        
    # tests remove_from_roster function
    def test_remove_from_roster(self):
        member = RosterMember.objects.create(name="test", roster=self.roster)
        path = reverse('remove_from_roster', kwargs=dict(roster_id=self.roster.pk, member_id=member.pk))
        referer = reverse('roster', kwargs=dict(roster_id=self.roster.pk))
        response = self.client.get(path, HTTP_REFERER=referer, follow=True)
        self.assertEqual(self.roster.members.count(), 0)
        self.assertNotContains(response, "test</td>")
    
    # test add_roster_to_events function
    def test_add_roster_to_events(self):
        path = reverse('add_roster_to_events', kwargs=dict(roster_id=1))
        s = SocialEvent.objects.create()
        RosterMember.objects.create(name="test", roster=self.roster)
        referer = reverse('roster', kwargs=dict(roster_id=1))

        # contains the name of all checked events, default name for an event is test
        post_data = {
            'event_checkboxes': 'test'
        }
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        s.refresh_from_db()
        self.assertContains(response, "The members of this roster were successfully added to the following event:</b> test")
        self.assertEqual(s.list.count(), 1)

    # shouldn't behave differently, but shouldn't add duplicates to the event
    def test_add_roster_to_events(self):
        path = reverse('add_roster_to_events', kwargs=dict(roster_id=1))
        s = SocialEvent.objects.create()
        Attendee.objects.create(name="test", user="admin", event=s)
        RosterMember.objects.create(name="test", roster=self.roster)
        referer = reverse('roster', kwargs=dict(roster_id=1))

        # contains the name of all checked events, default name for an event is test
        post_data = {
            'event_checkboxes': 'test'
        }
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        s.refresh_from_db()
        self.assertContains(response, "The members of this roster were successfully added to the following event:</b> test")
        self.assertEqual(s.list.count(), 1)

    # test add_roster_to_events with get request, should return 404
    def test_add_roster_to_events_get(self):
        path = reverse('add_roster_to_events', kwargs=dict(roster_id=1))
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    # test save_as_roster view
    def test_save_as_roster(self):
        s = SocialEvent.objects.create()
        path = reverse('save_as_roster', kwargs=dict(event_id=s.pk))
        Attendee.objects.create(name="test", user="admin", event=s)
        post_data = {
            'roster_name': 'saved_roster'
        }
        referer = reverse('social_event', kwargs=dict(event_id=s.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "List successfully saved as roster: saved_roster")
        self.assertTrue(Roster.objects.get(title="saved_roster"))
        self.assertEqual(Roster.objects.get(title="saved_roster").members.count(), 1)
        self.assertTrue(Roster.objects.get(title="saved_roster").members.get(name="test"))

    # test save_as_roster view with get method, which should return 404
    def test_save_as_roster_get(self):
        s = SocialEvent.objects.create()
        path = reverse('save_as_roster', kwargs=dict(event_id=s.pk))
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
    
    # tests create_roster function
    def test_create_roster(self):
        path = reverse('create_roster')
        post_data = {
            'title': 'created_roster',
            'members': 'test1\ntest2\ntest3'
        }
        referer = reverse('social')
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "created_roster</a>")
        self.assertTrue(Roster.objects.get(title="created_roster"))
        self.assertEqual(Roster.objects.get(title="created_roster").members.count(), 3)

    # tests create_roster with duplicates
    def test_create_roster_duplicates(self):
        path = reverse('create_roster')
        post_data = {
            'title': 'created_roster',
            'members': 'test1\ntest2\ntest1'
        }
        referer = reverse('social')
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "created_roster</a>")
        self.assertTrue(Roster.objects.get(title="created_roster"))
        self.assertEqual(Roster.objects.get(title="created_roster").members.count(), 2)

    # tests create_roster function under get request, should be 404
    def test_create_roster_get(self):
        path = reverse('create_roster')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    # tests remove_roster function
    def test_remove_roster(self):
        path = reverse('remove_roster', kwargs=dict(roster_id=self.roster.pk))
        referer = reverse('social')
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertNotContains(response, "test_roster</a>")
        self.assertFalse(Roster.objects.filter(id=1))

    