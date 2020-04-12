from django.test import TestCase
from django.contrib.auth.models import User
from .models import *
from django.urls import reverse
from . import views
from .forms import *
from datetime import date, timedelta
from django.utils import timezone


# Create your tests here.

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
