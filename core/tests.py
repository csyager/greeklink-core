from django.test import TestCase, Client
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import *
from django.urls import reverse
from . import views
from .forms import *
from datetime import date, timedelta
from django.utils import timezone
from .views import getSettings
import re


# Create your tests here.

# tests users signing in, out, and registering
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
        

class AnnouncementsTestCase(TestCase):
    def setUp(self):
        u = User.objects.create(username="admin", is_superuser=True)
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

    # tests that announcement form doesn't take valid input
    def test_add_announcement_form_invalid(self):
        form_data = {}
        form = AnnouncementForm(data=form_data)
        self.assertFalse(form.is_valid())


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
        self.assertNotContains(response, "<td>attendee1</td>")
        self.assertContains(response, "<td>attendee2</td>")
        path = reverse('remove_from_list', kwargs=dict(event_id=1, attendee_id=2))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertFalse(Attendee.objects.filter(name="attendee2"))
        self.assertNotContains(response, "<td>attendee2</td>")
        self.assertContains(response, "<td>attendee3</td>")

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