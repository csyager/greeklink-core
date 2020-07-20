from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime
from core.models import SocialEvent
from rush.models import RushEvent
from .models import ChapterEvent
from dateutil.relativedelta import relativedelta
from .forms import ChapterEventForm

class CalendarTestCase(TestCase):
    """ tests basic appearance and functionality of calendar """
    def setUp(self):
        self.user = User.objects.create(username='test')
        self.client.force_login(self.user)
        self.rush_event = RushEvent.objects.create(name="rush_test", date=datetime.today(), time=datetime.now(), location="test")
        self.social_event = SocialEvent.objects.create(name="social_test", date=datetime.today(), time=datetime.now(), location="test")
        self.chapter_event = ChapterEvent.objects.create(name="chapter_test", date=datetime.today(), time=datetime.now(), location="test")
    
    def test_calendar_template(self):
        """ tests that the current month appears by default """
        today = datetime.today()
        path = reverse('cal:index')
        response = self.client.post(path)
        self.assertContains(response, today.month)

    def test_rush_event_appears(self):
        """ tests that rush events are appearing on calendar """
        path = reverse('cal:index')
        response = self.client.post(path)
        self.assertContains(response, '<a href="/rush/events/' + str(self.rush_event.pk))

    def test_social_event_appears(self):
        """ tests that social events are appearing on calendar """
        path = reverse('cal:index')
        response = self.client.post(path)
        self.assertContains(response, '<a href="/social_event' + str(self.social_event.pk))

    def test_chapter_event_appears(self):
        """ tests that chapter events are appearing on calendar """
        path = reverse('cal:index')
        response = self.client.post(path)
        self.assertContains(response, 'chapter_test')

    def test_chapter_event_recurrence(self):
        """ tests that chapter events are recurring properly """
        ChapterEvent.objects.create_chapter_event(name="recurrence_test", date=datetime.today(), time=datetime.now(), location="test", recurring='Daily', start_date=datetime.today(), end_date=datetime.today()+relativedelta(days=+1))
        path = reverse('cal:index')
        response = self.client.post(path)
        self.assertContains(response, "recurrence_test", count=2)

    def test_month_overlap(self):
        """ tests that going to next month from december will run back to january """
        get_data = {
            'month': '13',
            'year': '2020'
        }
        path = reverse('cal:index')
        response = self.client.get(path, get_data)
        self.assertContains(response, 'January 2021')

    def test_month_underlap(self):
        """ tests that going to previous month from january will run back to december """
        get_data = {
            'month': '0',
            'year': '2020'
        }
        path = reverse('cal:index')
        response = self.client.get(path, get_data)
        self.assertContains(response, 'December 2019')

    def test_create_chapter_event_valid(self):
        """ tests creating chapter event from form data """
        post_data = {
            'name': 'test_chapter_event_create',
            'location': 'test',
            'date': datetime.date(datetime.today()),
            'time': '12:00',
            'recurring': 'None',
            'start_date': '',
            'end_date': ''
        }
        path = reverse('cal:create_chapter_event')
        referer = reverse('cal:index')
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, 'test_chapter_event_create')

    def test_create_chapter_event_invalid(self):
        """ tests creating chapter event with invalid data """
        post_data = {
            'name': 'test_chapter_event_create_invalid',
            'location': 'test',
            'date': '',
            'time': '12:00',
            'recurring': 'None',
            'start_date': '',
            'end_date': ''
        }   # date is a required field
        form = ChapterEventForm(post_data)
        self.assertFalse(form.is_valid())
        path = reverse('cal:create_chapter_event')
        referer = reverse('cal:index')
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, b'date')

    def test_create_chapter_event_recurring_no_end(self):
        """ tests creating a chapter event with a recurrence set but no end date """
        post_data = {
            'name': 'test_chapter_event_create_invalid',
            'location': 'test',
            'date': datetime.date(datetime.today()),
            'time': '12:00',
            'recurring': 'Daily',
            'start_date': '',
            'end_date': ''
        }   # end date is required if event is recurrent
        form = ChapterEventForm(post_data)
        self.assertFalse(form.is_valid())
        path = reverse('cal:create_chapter_event')
        referer = reverse('cal:index')
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, b'start_dateend_date')

    def test_create_chapter_event_get(self):
        """ test using get method on create_chapter_event """
        path = reverse('cal:create_chapter_event')
        referer = reverse('cal:index')
        response = self.client.get(path, HTTP_REFERER=referer, follow=True)
        self.assertEqual(response.status_code, 404)