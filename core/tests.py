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
        

    def test_resources_page_exists(self):
        self.client.force_login(self.regular)
        path = reverse('resources')
        response = self.client.post(path)
        self.assertContains(response, "Resources")

    def test_admin_load_link_alert(self):
        self.client.force_login(self.admin)
        path = reverse('resources')
        response = self.client.post(path)
        self.assertContains(response, "No Google Calendar loaded!")

    def test_google_calendar(self):
        self.client.force_login(self.admin)
        settings = getSettings()
        settings.calendar_embed = 'cal_link_here'
        settings.save()
        path = reverse('resources')
        response = self.client.post(path)
        self.assertNotContains(response, "No Google Calendar loaded!")

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

    def test_regular_users(self):
        self.client.force_login(self.regular)
        path = reverse('resources')
        response = self.client.post(path)
        self.assertNotContains(response, "No Google Calendar loaded!")
        self.assertNotContains(response, "Upload File")
        self.assertNotContains(response, "Add link")
        self.assertNotContains(response, "modal")

    def test_file_upload(self):
        self.client.force_login(self.admin)
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'description': 'file description'}
        file_dict = {'file': file}
        form = UploadFileForm(post_dict, file_dict)
        self.assertTrue(form.is_valid())

    def test_file_upload_view(self):
        self.client.force_login(self.admin)
        file = SimpleUploadedFile("file.txt", b"file_content", content_type="text/plain")
        post_dict = {'name': 'filename', 'file': file, 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict, follow=True)
        self.assertContains(response, 'filename')

    def test_file_upload_errors(self):
        self.client.force_login(self.admin)
        post_dict = {'name': 'filename', 'description': 'file description'}
        path = reverse('upload_file')
        response = self.client.post(path, post_dict)
        self.assertContains(response, b'file')

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

    def test_add_calendar(self):
        self.client.force_login(self.admin)
        path = reverse('addCal')
        post_dict = {'cal_embed_link': 'hyperlink'}
        response = self.client.post(path, post_dict, follow=True)
        settings = getSettings()
        self.assertEqual(settings.calendar_embed, 'hyperlink')

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
        
    def test_social_home_template(self):
        path = reverse('social')
        response = self.client.post(path)
        self.assertContains(response, "<h1>Social</h1>")

    def test_event_on_home_page(self):
        path = reverse('social')
        response = self.client.post(path)
        self.assertContains(response, '<a href="social_event1"')
    
    def test_create_event(self):
        path = reverse('create_social_event')
        post_dict = {'name': 'test_name', 'date': '2001-01-01', 'time': '12:00', 'location': ""}
        response = self.client.post(path, post_dict, HTTP_REFERER=reverse('social'), follow=True)
        self.assertContains(response, 'test_name -- Jan. 1, 2001, noon')

    def test_social_event_page_exists(self):
        path = reverse('social_event', kwargs=dict(event_id=1))
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        