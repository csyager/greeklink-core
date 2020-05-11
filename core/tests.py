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
from .views import getSettings
from .tokens import *
import re
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


# Create your tests here.

# tests users signing in, out, and registering
# TODO:  This needs to be massively expanded once we get auth figured out
class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.u = User.objects.create(username="admin", is_superuser=True)
        self.client.force_login(self.u)

    # tests that logged in user can logout
    def test_logout_redirects_to_login(self):
        path = reverse('logout')
        response = self.client.post(path, follow=True)
        self.assertContains(response, 'Login')


class ResourcesTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.regular = User.objects.create(username="regular")
        
    # tests that resources page exists with proper header
    def test_resources_page_exists(self):
        self.client.force_login(self.regular)
        path = reverse('resources')
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resources")

    # tests that for an admin user the alert giving the option to load a google calendar appears
    def test_admin_load_link_alert(self):
        self.client.force_login(self.admin)
        path = reverse('resources')
        response = self.client.post(path)
        self.assertContains(response, "No Google Calendar loaded!")

    # tests that adding a google calendar makes the alert disappear
    def test_google_calendar_alert_disappears(self):
        self.client.force_login(self.admin)
        settings = getSettings()
        settings.calendar_embed = 'cal_link_here'
        settings.save()
        path = reverse('resources')
        response = self.client.post(path)
        self.assertNotContains(response, "No Google Calendar loaded!")

    # tests that all admin options appear on the resources page
    def test_admin_controls(self):
        self.client.force_login(self.admin)
        settings = getSettings()
        settings.calendar_embed = 'cal_link_here'
        settings.save()
        path = reverse('resources')
        response = self.client.post(path)
        self.assertContains(response, "Remove Calendar")
        self.assertContains(response, "Upload File")
        self.assertContains(response, "Add link")
        self.assertContains(response, "modal")

    # tests that admin options do not appear for users without admin privileges
    def test_regular_users(self):
        self.client.force_login(self.regular)
        path = reverse('resources')
        response = self.client.post(path)
        self.assertNotContains(response, "No Google Calendar loaded!")
        self.assertNotContains(response, "Upload File")
        self.assertNotContains(response, "Add link")
        self.assertNotContains(response, "modal")

    # tests resource file upload form
    def test_file_upload(self):
        self.client.force_login(self.admin)
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'description': 'file description'}
        file_dict = {'file': file}
        form = UploadFileForm(post_dict, file_dict)
        self.assertTrue(form.is_valid())

    # tests resource file upload function
    def test_file_upload_view(self):
        self.client.force_login(self.admin)
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'file': file, 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict, follow=True)
        self.assertContains(response, 'filename')

    # tests error messages in file upload form
    def test_file_upload_errors(self):
        self.client.force_login(self.admin)
        post_dict = {'name': 'filename', 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict)
        self.assertContains(response, b'file')

    # tests remove file function
    def test_remove_file(self):
        self.client.force_login(self.admin)
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'file': file, 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict, follow=True)
        self.assertContains(response, 'filename')
        path = reverse('remove_file', kwargs=dict(file_id=1))
        response = self.client.post(path, follow=True)
        self.assertNotContains(response, 'filename')

    # tests the add calendar function
    def test_add_calendar(self):
        self.client.force_login(self.admin)
        path = reverse('addCal')
        post_dict = {'cal_embed_link': 'hyperlink'}
        response = self.client.post(path, post_dict, follow=True)
        settings = getSettings()
        self.assertEqual(settings.calendar_embed, 'hyperlink')

    # tests the remove calendar function
    def test_remove_calendar(self):
        self.client.force_login(self.admin)
        settings = getSettings()
        settings.calendar_embed = 'hyperlink'
        settings.save()
        path = reverse('removeCal')
        response = self.client.post(path)
        settings.refresh_from_db()
        self.assertEqual(settings.calendar_embed, '')

    # tests the add_link views.py function
    def test_add_link_view(self):
        self.client.force_login(self.admin)
        post_dict = {'name': 'test', 'description': 'test description', 'url': 'https://www.google.com'}
        path = reverse('add_link')
        referer = reverse('resources')
        response = self.client.post(path, post_dict, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, '<a href="https://www.google.com"')
        
    # tests the link form
    def test_add_link_form_valid(self):
        self.client.force_login(self.admin)
        form_data = {'name': 'test', 'description': 'test description', 'url': 'https://www.google.com'}
        form = LinkForm(data=form_data)
        self.assertTrue(form.is_valid)

    # tests when the link form is invalid
    def test_add_link_form_invalid(self):
        self.client.force_login(self.admin)
        form_data = {}
        form = LinkForm(data=form_data)
        self.assertFalse(form.is_valid())

    # tests that errors are returned when link form is invalid
    def test_add_link_form_errors(self):
        self.client.force_login(self.admin)
        post_dict = {}
        path = reverse('add_link')
        response = self.client.post(path, post_dict)
        self.assertContains(response, 'nameurldescription')

    # tests remove link function
    def test_remove_link(self):
        self.client.force_login(self.admin)
        ResourceLink.objects.create(name='test', description='test description', url='https://www.google.com')
        path = reverse('remove_link', kwargs=dict(link_id=1))
        referer = reverse('resources')
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(ResourceLink.objects.all())
        self.assertFalse(re.findall("<h4.*test</h4", str(response.content)))
        
class AnnouncementsTestCase(TestCase):
    def setUp(self):
        u = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.client.force_login(u)
        a = Announcement.objects.create(user=u)

    # tests that announcement is displayed on index
    def test_announcement_appears(self):
        path = reverse('index')
        response = self.client.post(path)
        self.assertContains(response, '<li class="list-group-item">')

    # tests that announcement link works
    def test_announcement_link_appears(self):
        a = Announcement.objects.get(title="test")
        a.target = reverse('resources')
        a.save()
        path = reverse('index')
        response = self.client.post(path)
        self.assertContains(response, '<a href="' + reverse('resources'))

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
        response = self.client.post(path, post_dict, follow=True)
        self.assertContains(response, 'titlebody')


class SocialTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        self.client.force_login(self.admin)
        SocialEvent.objects.create()
        
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
        self.assertContains(response, '<a href="social_event1"')
    
    # tests the create event function
    def test_create_event(self):
        path = reverse('create_social_event')
        post_dict = {'name': 'test_name', 'date': '2001-01-01', 'time': '12:00', 'location': ""}
        response = self.client.post(path, post_dict, HTTP_REFERER=reverse('social'), follow=True)
        self.assertContains(response, 'test_name -- Jan. 1, 2001, noon')

    # tests that the page for an individual social event exists
    def test_social_event_page_exists(self):
        path = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
    
    # tests that the social event page populates with relevant data
    def test_social_event_page_populates(self):
        path = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path)
        content = str(response.content)
        self.assertTrue(re.findall('<h1.*test</h1>', content))
        self.assertContains(response, "Jan. 1, 2000, noon")

    # tests the remove_social_event function
    def test_remove_social_event(self):
        path = reverse('remove_social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, HTTP_REFERER=reverse('social'), follow=True)
        self.assertNotContains(response, "test_name -- Jan. 1, 2001, noon")
        self.assertRaises(SocialEvent.DoesNotExist, SocialEvent.objects.get, id=1)

    # tests that the add_to_list function works with both individual and multiple input
    def test_add_to_list_individual_and_multiple(self):
        path = reverse('add_to_list', kwargs=dict(event_id=1))
        post_data = {'multiple_names': 'many_name1\nmany_name2\nmany_name3', 'name': 'individual_name'}
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, post_data, HTTP_REFERER=referer)
        self.assertTrue(Attendee.objects.filter(name="many_name1"))
        self.assertTrue(Attendee.objects.filter(name="many_name2"))
        self.assertTrue(Attendee.objects.filter(name="many_name3"))
        self.assertTrue(Attendee.objects.filter(name="individual_name"))

    # tests that add_to_list function works with only individual input
    def test_add_to_list_individual(self):
        path = reverse('add_to_list', kwargs=dict(event_id=1))
        post_data = {'multiple_names': '', 'name': 'individual_name'}
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, post_data, HTTP_REFERER=referer)
        self.assertTrue(Attendee.objects.filter(name="individual_name"))
        self.assertFalse(Attendee.objects.filter(name="many_name"))

    # tests that add_to_list function works with only multiple-name input
    def test_add_to_list_multiple(self):
        path = reverse('add_to_list', kwargs=dict(event_id=1))
        post_data = {'multiple_names': 'many_name1\nmany_name2\nmany_name3', 'name': ''}
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, post_data, HTTP_REFERER=referer)
        self.assertTrue(Attendee.objects.filter(name="many_name1"))
        self.assertTrue(Attendee.objects.filter(name="many_name2"))
        self.assertTrue(Attendee.objects.filter(name="many_name3"))
        self.assertFalse(Attendee.objects.filter(name="individual_name"))

    # tests remove_from_list feature to make sure attendees are removed from database and UI
    def test_remove_from_list(self):
        event = SocialEvent.objects.get(id=1)
        for i in range(1, 4):
            a = Attendee.objects.create(name="attendee" + str(i), user=self.admin)
            event.list.add(a)
        event.save()
        path = reverse('remove_from_list', kwargs=dict(event_id=1, attendee_id=1))
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(Attendee.objects.filter(name="attendee1"))
        self.assertFalse(re.findall("<td.*>attendee1</td>", str(response.content)))
        self.assertTrue(re.findall("<td.*>attendee2</td>", str(response.content)))
        path = reverse('remove_from_list', kwargs=dict(event_id=1, attendee_id=2))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(Attendee.objects.filter(name="attendee2"))
        self.assertFalse(re.findall("<td.*>attendee2</td>", str(response.content)))
        self.assertTrue(re.findall("<td.*>attendee3</td>", str(response.content)))

    # tests clear list feature
    def test_clear_list(self):
        event = SocialEvent.objects.get(id=1)
        for i in range(1, 4):
            a = Attendee.objects.create(name="attendee" + str(i), user=self.admin)
            event.list.add(a)
        event.save()
        path = reverse('clear_list', kwargs=dict(event_id=1))
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        content = str(response.content)
        self.assertFalse(re.findall("<td>attendee[1-3]</td>", content))
        self.assertFalse(event.list.all())

    # tests exporting a spreadsheet of attendees
    def test_export_xls(self):
        event = SocialEvent.objects.get(id=1)
        for i in range(0, 3):
            a = Attendee.objects.create(name="attendee" + str(i), user=self.admin)
            event.list.add(a)
        event.save()
        path = reverse('export_xls', kwargs=dict(event_id=1))
        response = self.client.post(path)
        self.assertEqual(response.get('Content-Type'), 'application/ms-excel')
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename=1_attendance.xls')

    # tests adding single duplicate name to the list
    def test_add_individual_duplicate(self):
        event = SocialEvent.objects.get(id=1)
        a = Attendee.objects.create(name="attendee", user=self.admin)
        event.list.add(a)
        path = reverse('add_to_list', kwargs=dict(event_id=1))
        # should fail, because name is a duplicate
        post_data = {'multiple_names': '', 'name': 'attendee'}
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertTrue(re.findall("The following names were not added to the list", str(response.content)))
        self.assertTrue(re.findall("<li.*>attendee</li>", str(response.content)))
        self.assertEqual(len(Attendee.objects.filter(name="attendee")), 1)

    # tests adding multiple duplicate names to the list
    def test_add_multiple_duplicate(self):
        event = SocialEvent.objects.get(id=1)
        for i in range(1, 3):
            a = Attendee.objects.create(name="attendee" + str(i), user=self.admin)
            event.list.add(a)
        path = reverse('add_to_list', kwargs=dict(event_id=1))
        # should fail, because both names are duplicates
        post_data = {'multiple_names': 'attendee1\nattendee2', 'name': ''}
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertTrue(re.findall("The following names were not added to the list", str(response.content)))
        self.assertTrue(re.findall("<li.*>attendee1</li>", str(response.content)))
        self.assertTrue(re.findall("<li.*>attendee2</li>", str(response.content)))
        self.assertEqual(len(Attendee.objects.filter(name="attendee1")), 1)
        self.assertEqual(len(Attendee.objects.filter(name="attendee2")), 1)
    
    # tests adding multiple names where some are duplicates and some aren't
    def test_add_duplicates_and_new(self):
        event = SocialEvent.objects.get(id=1)
        a = Attendee.objects.create(name="attendee1", user=self.admin)
        event.list.add(a)
        path = reverse('add_to_list', kwargs=dict(event_id=1))
        # one should fail, one should work
        post_data = {'multiple_names': 'attendee1\nattendee2', 'name': ''}
        referer = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertTrue(re.findall("The following names were not added to the list", str(response.content)))
        self.assertTrue(re.findall("<li.*>attendee1</li>", str(response.content)))
        self.assertFalse(re.findall("<li.*>attendee2</li>", str(response.content)))
        self.assertEqual(len(Attendee.objects.filter(name="attendee1")), 1)
        self.assertEqual(len(Attendee.objects.filter(name="attendee2")), 1)

    # tests checking attendance feature
    def test_check_attendance(self):
        event = SocialEvent.objects.get(id=1)
        a = Attendee.objects.create(name="attendee", user=self.admin)
        event.list.add(a)
        path = reverse('check_attendee')
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
        event = SocialEvent.objects.get(id=1)
        a = Attendee.objects.create(name="attendee", user=self.admin, attended=True)
        event.list.add(a)
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
        event = SocialEvent.objects.get(id=1)
        # create three attendees and add to list
        # by default, all new attendees have attended=False
        for i in range(0, 3):
            a = Attendee.objects.create(name="attendee" + str(i), user=self.admin)
            event.list.add(a)
        path = reverse('refresh_attendees')
        get_data = {'event_id': event.id}
        response = self.client.get(path, get_data)
        self.assertEqual(response.status_code, 200)
        # response should be false for all three attendees, with ids from 1 to 3 inclusive
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                str(1): False,
                str(2): False,
                str(3): False
            }
        )
    
    # tests refresh_attendees view when status of attendee changes, to ensure change is propogated
    def test_refresh_attendees_dynamic(self):
        event = SocialEvent.objects.get(id=1)
        for i in range(0, 3):
            a = Attendee.objects.create(name="attendee" + str(i), user=self.admin)
            event.list.add(a)
        path = reverse('refresh_attendees')
        get_data = {'event_id': event.id}
        response = self.client.get(path, get_data)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                str(1): False,
                str(2): False,
                str(3): False
            }
        )

        # change one of the attendees, to see if the refresh changes the JSON response
        a = Attendee.objects.get(id=2)
        a.attended = True
        a.save()

        response = self.client.get(path, get_data)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                str(1): False,
                str(2): True,
                str(3): False
            }
        )

    # test toggle_party_mode view
    def test_toggle_party_mode_view(self):
        # event.party_mode is initially false, request should make it true
        path = reverse('toggle_party_mode', kwargs=dict(event_id=1))
        response = self.client.post(path)
        event = SocialEvent.objects.get(id=1)
        self.assertTrue(event.party_mode)

        # sending request again should make event.party_mode false again
        response = self.client.post(path)
        event.refresh_from_db()
        self.assertFalse(event.party_mode)

    # test toggle_party_mode template
    def test_toggle_party_mode_template(self):
        # party mode should initially be false
        referer = reverse('social_event', kwargs=dict(event_id=1))
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
        path = reverse('toggle_party_mode', kwargs=dict(event_id=1))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        
        # when party mode is on, the label by the button should say on
        self.assertContains(response, "Party mode on")
        # The attended column should be present
        self.assertContains(response, "Attended")
        # the ajax script refreshing the list should be linked
        self.assertTrue(re.findall('<script src=".*cross_off_list.js', str(response.content)))
        # the add to list form should not be available
        self.assertNotContains(response, "Type Full Name Here")
        

class AuthenticationTestCase(TestCase):
    # def setUp(self):

    # gets template with signup form
    def test_signup_get_template(self):
        path = reverse('signup')
        response = self.client.get(path)
        self.assertContains(response, "Register")

    # tests that signup form accepts valid input
    def test_signup_form(self):
        form_data = {
            'username': 'test',
            'email': 'test@test.com',
            'first_name': 'Test_first',
            'last_name': 'Test_last',
            'verification_key': '9999',
            'password1': 'c0mpl#x_p@$$w0rd',
            'password2': 'c0mpl#x_p@$$w0rd'
        }

        form = SignupForm(form_data)
        self.assertTrue(form.is_valid())

    # tests that form rejects passwords that are too simple
    def test_simple_password(self):
        form_data = {
            'username': 'test',
            'email': 'test@test.com',
            'first_name': 'Test_first',
            'last_name': 'Test_last',
            'verification_key': '9999',
            'password1': 'password',
            'password2': 'password'
        }
        form = SignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('This password is too common', form.errors['password2'][0])

    # tests that form rejects passwords that don't match
    def test_passwords_not_match(self):
        form_data = {
            'username': 'test',
            'email': 'test@test.com',
            'first_name': 'Test_first',
            'last_name': 'Test_last',
            'verification_key': '9999',
            'password1': 'password1',
            'password2': 'password2'
        }
        form = SignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual("The two password fields didn’t match.", form.errors['password2'][0])

    # tests that form rejects usernames that are already in use
    def test_username_already_taken(self):
        User.objects.create(username="test")
        form_data = {
            'username': 'test',
            'email': 'test@test.com',
            'first_name': 'Test_first',
            'last_name': 'Test_last',
            'verification_key': '9999',
            'password1': 'c0mpl#x_p@$$w0rd',
            'password2': 'c0mpl#x_p@$$w0rd'
        }
        form = SignupForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual("A user with that username already exists.", form.errors['username'][0])

    # tests that the user is redirected to successful verification page
    def test_valid_input_template(self):
        post_data = {
            'username': 'test',
            'email': 'test@test.com',
            'first_name': 'Test_first',
            'last_name': 'Test_last',
            'verification_key': '9999',
            'password1': 'c0mpl#x_p@$$w0rd',
            'password2': 'c0mpl#x_p@$$w0rd'
        }
        path = reverse('signup')
        response = self.client.post(path, post_data)

        self.assertContains(response, "Thank you for signing up for GreekLink")

    # tests that inactive users can activate with activate view
    def test_activate_view(self):
        user = User.objects.create(username="test", is_active="False")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        path = reverse('activate', kwargs=dict(uidb64=uidb64, token=token))
        response = self.client.post(path)
        self.assertContains(response, "Your account has been verified!")

    # tests user that does not exist
    def test_activate_user_does_not_exist(self):
        user = User.objects.create(username="test", is_active="False")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        path = reverse('activate', kwargs=dict(uidb64=uidb64, token=token))
        user.delete()
        response = self.client.post(path)
        self.assertContains(response, "Activation link is invalid")

    # tests invalid activation token
    def test_activate_user_invalid_token(self):
        user = User.objects.create(username="test", is_active="False")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = "999-99999999999999999999"
        path = reverse('activate', kwargs=dict(uidb64=uidb64, token=token))
        response = self.client.post(path)
        self.assertContains(response, "Activation link is invalid")

    # tests logout
    def test_logout(self):
        user = User.objects.create(username="test")
        self.client.force_login(user)
        path = reverse('logout')
        response = self.client.post(path, follow=True)
        self.assertContains(response, "Login")