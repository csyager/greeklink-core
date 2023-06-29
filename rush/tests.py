from django.test import TestCase
from rush.models import Rushee, Comment, RushEvent
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import RusheeForm, CommentForm
from django.http import HttpResponse
from core.views import getSettings
from tenant_schemas.test.cases import TenantTestCase
from tenant_schemas.test.client import TenantClient

# Create your tests here.

class RusheeTestCase(TenantTestCase):
    """ Tests the basic parts of the rushee view and template """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.u = User.objects.create(username="test_user", is_staff=True)
        self.client.force_login(self.u)
        self.rushee = Rushee.objects.create(name="test")

    def test_rushee_personal_information(self):
        """ tests that personal information appears in template """
        self.rushee.email = "test@test.com"
        self.rushee.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path)
        self.assertContains(response, '<td>test</td>')
        self.assertContains(response, '<td>test@test.com</td>')

    def test_rushee_comments_appear(self):
        """ tests that comments appear in template """
        Comment.objects.create(name="first last", body="test comment", rushee=self.rushee)
        path = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path)
        self.assertContains(response, 'first last')
        self.assertContains(response, 'test comment')

    def test_post_comment(self):
        """ tests post_comment function """
        post_data = {
            'body': 'this is a test comment'
        }
        path = reverse('rush:comment', kwargs=dict(rushee_id=self.rushee.pk))
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, 'this is a test comment')

    def test_post_comment_form_errors(self):
        """ tests post_comment function with form errors """
        post_data = {
            'body': 'x' * 281
        }
        path = reverse('rush:comment', kwargs=dict(rushee_id=self.rushee.pk))
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path, post_data, HTTP_REFERER=referer, follow=True)
        self.assertEqual(response.content, b'Comment not recorded.')

    def test_remove_comment(self):
        """ tests remove_comment function """
        comment = Comment.objects.create(name="first last", body="test comment", rushee=self.rushee)
        path = reverse('rush:remove_comment', kwargs=dict(comment_id=comment.pk))
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertNotContains(response, 'test comment')

    def test_endorse(self):
        """ tests endorse function """
        path = reverse('rush:endorse', kwargs=dict(rushee_id=self.rushee.pk))
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "You have <b>endorsed</b> this rushee")

    def test_oppose(self):
        """ tests oppose function """
        path = reverse('rush:oppose', kwargs=dict(rushee_id=self.rushee.pk))
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "You have <b>opposed</b> this rushee")

    def test_clear_endorsements(self):
        """ tests clear endorsements function """
        self.rushee.endorsements.add(self.u)
        path = reverse('rush:clear_endorsement', kwargs=dict(rushee_id=self.rushee.pk))
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertNotContains(response, "You have <b>endorsed</b> this rushee")


class IndexTestCase(TenantTestCase):
    """ tests the index page of the recruitment tab """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.u = User.objects.create(username="test_user")
        self.client.force_login(self.u)
        self.event1 = RushEvent.objects.create(name='test_event1', date='2001-01-01', time='00:00:00', round=1, new_rushees_allowed=True)
        self.event2 = RushEvent.objects.create(name='test_event2', date='2001-01-01', time='00:00:00', round=3, new_rushees_allowed=True)

    def test_index_health(self):
        path = reverse('rush:index')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_index_round_groups(self):
        path = reverse('rush:index')
        response = self.client.get(path)
        self.assertContains(response, "<h4>Round 1</h4>")
        self.assertContains(response, "<h4>Round 3</h4>")

class RusheeFilterTestCase(TenantTestCase):
    """ tests the filter function for the rushee template """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.u = User.objects.create(username="test_user")
        self.client.force_login(self.u)
        self.r1 = Rushee.objects.create(name="test1")
        self.r2 = Rushee.objects.create(name="test2")

    def test_next_rushee_button_no_filter(self):
        """ tests next button when the filter is not set """
        path = reverse('rush:rushee', kwargs=dict(num=self.r1.pk))
        response = self.client.post(path)
        self.assertContains(response, '<a href="/rush/rushee' + str(self.r2.pk) + '" id="next-rushee"')
    
    def test_next_rushee_filter(self):
        """ tests next button when filter is set """
        session = self.client.session
        session['rushee_filter'] = dict(name='test1')
        session.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.r1.pk))
        response = self.client.post(path)
        self.assertNotContains(response, '<a href="/rush/rushee' + str(self.r2.pk) + '" id="next-rushee"')

    def test_prev_rushee_button_no_filter(self):
        """ tests previous button when filter is not set """
        path = reverse('rush:rushee', kwargs=dict(num=self.r2.pk))
        response = self.client.post(path)
        self.assertContains(response, '<a href="/rush/rushee' + str(self.r1.pk) + '" id="prev-rushee"')

    def test_prev_rushee_filter(self):
        """ tests previous button when the filter is set """
        session = self.client.session
        session['rushee_filter'] = dict(name='test2')
        session.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.r2.pk))
        response = self.client.post(path)
        self.assertNotContains(response, '<a href="/rush/rushee' + str(self.r1.pk) + '" id="prev-rushee"')

    def test_cut_filter_on_next(self):
        """ tests the next button when the cut filter is set """
        self.r2.cut = True
        self.r2.save()
        session = self.client.session
        session['rushee_filter'] = dict(cut=True)
        session.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.r1.pk))
        response = self.client.post(path)
        self.assertContains(response, '<a href="/rush/rushee' + str(self.r2.pk) + '" id="next-rushee"')

    def test_cut_filter_on_prev(self):
        """ tests the previous button when the cut filter is set """
        self.r1.cut = True
        self.r1.save()
        session = self.client.session
        session['rushee_filter'] = dict(cut=True)
        session.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.r2.pk))
        response = self.client.post(path)
        self.assertContains(response, '<a href="/rush/rushee' + str(self.r1.pk) + '" id="prev-rushee"')

    def test_cut_filter_off_next(self):
        """ tests the next button when the cut filter is off """
        self.r2.cut = True
        self.r2.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.r1.pk))
        response = self.client.post(path)
        self.assertNotContains(response, '<a href="/rush/rushee' + str(self.r2.pk) + '" id="next-rushee"')

    def test_cut_filter_off_prev(self):
        """ tests the previous button when the cut filter is off """
        self.r1.cut = True
        self.r1.save()
        path = reverse('rush:rushee', kwargs=dict(num=self.r2.pk))
        response = self.client.post(path)
        self.assertNotContains(response, '<a href="/rush/rushee' + str(self.r1.pk) + '" id="prev-rushee"')

    def test_set_filter(self):
        post_data = {
            'name': 'test'
        }
        path = reverse('rush:filter_rushees')
        self.client.post(path, post_data)
        session = self.client.session
        self.assertEqual(session['rushee_filter'], dict(name='test'))

    def test_set_filter_get(self):
        path = reverse('rush:filter_rushees')
        request = self.client.get(path)
        self.assertEqual(request.status_code, 404)

    def test_set_filter_empty(self):
        """ tests setting filter with empty post """
        post_data = {}
        path = reverse('rush:filter_rushees')
        self.client.post(path, post_data)
        try:
            filter = self.client.session['rushee_filter']
            self.fail("session['rushee_filter'] object should not exist")
        except KeyError:
            pass

    def test_set_filter_form_errors(self):
        """ tests setting filter with form errors - major is too long """
        post_data = {
            'major': 'abcdefghijklmnopqrstuvwxyz'
        }
        path = reverse('rush:filter_rushees')
        response = self.client.post(path, post_data)
        self.assertEqual(response.content, b'major')

    def test_remove_filter(self):
        self.client.session['rushee_filter'] = dict(name='test')
        self.client.session.save()
        path = reverse('rush:clear_rushees_filter')
        self.client.post(path)
        try:
            filter = self.client.session['rushee_filter']
            self.fail("session['rushee_filter'] object should not exist")
        except KeyError:
            pass


class RusheeRegisterTestCase(TenantTestCase):
    """ tests rushee register function """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = User.objects.create(username="test_user")
        self.client.force_login(self.user)
        self.event = RushEvent.objects.create(name='test_event', date='2001-01-01', time='00:00:00', round=1, new_rushees_allowed=True)
        self.form_data = {
            'name': 'test_name',
            'email': 'test@test.com',
            'year': '1',
            'major': 'test_major',
            'hometown': 'test_hometown',
            'address': 'test_address',
            'phone_number': '9999999999',
            'in_person': True
        }

    def test_valid_form_register(self):
        """ tests register function when form is valid """
        post_data = self.form_data
        self.assertTrue(RusheeForm(post_data).is_valid())
        path = reverse('rush:register', kwargs=dict(event_id=self.event.pk))
        self.client.post(path, post_data)
        self.assertTrue(Rushee.objects.get(name="test_name"))

    def test_invalid_form_register(self):
        """ tests register function when form is invalid """
        post_data = self.form_data
        post_data['email'] = 'invalid email'
        form = RusheeForm(data=post_data)
        path = reverse('rush:register', kwargs=dict(event_id=self.event.pk))
        response = self.client.post(path, post_data)
        test_response = HttpResponse(form.errors.as_data())
        self.assertEqual(response.content, test_response.content)
        try:
            Rushee.objects.get(name='test_name')
            self.fail("Rushee was created when it shouldn't have been.")
        except Rushee.DoesNotExist:
            pass

class SigninTestCase(TenantTestCase):
    """ test cases for the signin module """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = User.objects.create(username="test_user")
        self.client.force_login(self.user)
        settings = getSettings()
        settings.rush_signin_active = True
        settings.save()
        self.rushee = Rushee.objects.create(name='test_rushee')
        self.event1 = RushEvent.objects.create(name='first_event', date='2001-01-01', time='00:00:00', round=1, new_rushees_allowed=True)
        self.event2 = RushEvent.objects.create(name='second_event', date='2001-01-02', time='00:00:00', round=1, new_rushees_allowed=False)

    def test_signin_page_first_event(self):
        """ tests that the signin view redirects to the first event by default """
        path = reverse('rush:signin')
        response = self.client.post(path)
        self.assertContains(response, 'first_event')

    def test_signin_page_not_default_event(self):
        """ tests that the signin view directs to the correct event when parameter provided """
        path = reverse('rush:signin', kwargs=dict(event_id=self.event2.pk))
        response = self.client.post(path)
        self.assertContains(response, 'second_event')

    def test_signin_page_new_rushees_allowed(self):
        """ tests that when new rushees are allowed in an event, signin page appears differently """
        path = reverse('rush:signin')
        response = self.client.post(path)
        self.assertContains(response, 'action="register')
        self.assertNotContains(response, 'Click on your name to sign in.')

    def test_signin_page_new_rushees_not_allowed(self):
        """ tests that when new rushees are not allowed in an event, signin page appears differently """
        path = reverse('rush:signin', kwargs=dict(event_id=self.event2.pk))
        response = self.client.post(path)
        self.assertContains(response, 'Click on your name to sign in.')
        self.assertNotContains(response, 'action="register')

    def test_click_to_signin_link(self):
        """ tests that rushees can click to signin to events """
        path = reverse('rush:signin', kwargs=dict(event_id=self.event2.pk))
        response = self.client.post(path)
        self.assertContains(response, "<tr onclick=\"window.location='/rush/attendance" + str(self.rushee.pk) + "/" + str(self.event2.pk) + "';")

    def test_attendance_view(self):
        """ tests the attendance view function """
        path = reverse('rush:attendance', kwargs=dict(rushee_id=1, event_id=2))
        response = self.client.post(path)
        self.assertTrue(RushEvent.objects.get(pk=2).attendance.get(name='test_rushee'))
        self.assertContains(response, "Thank you, test_rushee.  You're good to go!")

class EventsTestCase(TenantTestCase):
    """ tests events and related functions """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = User.objects.create(username="test_user", is_superuser=True, is_staff=True)
        self.client.force_login(self.user)
        settings = getSettings()
        settings.rush_signin_active = True
        settings.save()
        self.rushee1 = Rushee.objects.create(name="first_rushee")
        self.rushee2 = Rushee.objects.create(name="second_rushee")
        self.event1 = RushEvent.objects.create(name='first_event', date='2001-01-01', time='00:00:00', round=1, new_rushees_allowed=True)
        self.event2 = RushEvent.objects.create(name='second_event', date='2001-01-02', time='00:00:00', round=1, new_rushees_allowed=False)

    def test_events_view(self):
        """ tests the view showing all rush events """
        path = reverse('rush:events')
        response = self.client.post(path)
        self.assertContains(response, '<a href="/rush/events/' + str(self.event1.pk))
        self.assertContains(response, '<a href="/rush/events/' + str(self.event2.pk))

    def test_single_event_view(self):
        """ tests the view showing a single event """
        path = reverse('rush:event', kwargs=dict(event_id=self.event1.pk))
        response = self.client.post(path)
        self.assertContains(response, 'first_event')

    def test_event_attendance(self):
        """ tests that rushees in attendance are listed on event page """
        self.event1.attendance.add(self.rushee1)
        self.event1.save()
        path = reverse('rush:event', kwargs=dict(event_id=self.event1.pk))
        response = self.client.post(path)
        self.assertContains(response, "<tr onclick=\"window.location='/rush/rushee" + str(self.rushee1.pk))

    def test_create_event_new_rushees(self):
        """ tests create_event view """
        post_data = {
            'name': 'third_event',
            'date': '2001-01-03',
            'time': '00:00:00',
            'round': '1',
            'location': 'test_location',
            'new_rushees': ['true'],
        }
        path = reverse('rush:create_event')
        self.client.post(path, post_data)
        event = RushEvent.objects.get(name='third_event')
        self.assertTrue(event)
        path = reverse('rush:signin', kwargs=dict(event_id=event.pk))
        response = self.client.post(path)
        self.assertContains(response, 'action="register')

    def test_create_event_no_new_rushees(self):
        """ tests create_event view when new rushees are not allowed """
        post_data = {
            'name': 'third_event',
            'date': '2001-01-03',
            'time': '00:00:00',
            'round': '1',
            'location': 'test_location',
            'new_rushees': [],
        }
        path = reverse('rush:create_event')
        self.client.post(path, post_data)
        event = RushEvent.objects.get(name='third_event')
        self.assertTrue(event)
        path = reverse('rush:signin', kwargs=dict(event_id=event.pk))
        response = self.client.post(path)
        self.assertContains(response, 'Click on your name to sign in.')

    def test_create_event_get(self):
        """ tests for 404 error when request method is not post """
        path = reverse('rush:create_event')
        request = self.client.get(path)
        self.assertEqual(request.status_code, 404)

    def test_remove_event(self):
        """ tests remove event view function """
        path = reverse('rush:remove_event', kwargs=dict(event_id=2))
        request = self.client.post(path)
        try:
            rushee = RushEvent.objects.get(pk=2)
            self.fail("Rushee matching query should not exist")
        except RushEvent.DoesNotExist:
            pass
    
    def test_round_headers_for_events_list(self):
        """ tests that proper round headers appear on events page"""
        path = reverse('rush:events')
        response = self.client.get(path)
        self.assertContains(response, "<h4>Round 1</h4>")
        self.assertNotContains(response, "<h4>Round 2</h4>")
    
    def test_round_headers_split_rounds(self):
        """ tests that proper round headers appear even if they are separated by a round"""
        RushEvent.objects.create(name='first_event', date='2001-01-01', time='00:00:00', round=3, new_rushees_allowed=True)
        path = reverse('rush:events')
        response = self.client.get(path)
        self.assertContains(response, "<h4>Round 1</h4>")
        self.assertNotContains(response, "<h4>Round 2</h4>")
        self.assertContains(response, "<h4>Round 3</h4>")
        
class CurrentRusheesTestCase(TenantTestCase):
    """ tests for the current rushees page """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = User.objects.create(username="test_user")
        self.client.force_login(self.user)
        self.rushee1 = Rushee.objects.create(name="first_rushee")
        self.rushee2 = Rushee.objects.create(name="second_rushee", cut=True)
        self.rushee3 = Rushee.objects.create(name="third_rushee")

    def test_current_rushees_template(self):
        """ tests that current rushees page displays with all rushees """
        path = reverse('rush:current_rushees')
        response = self.client.post(path)
        self.assertContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee1.pk))
        self.assertNotContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee2.pk))
        self.assertContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee3.pk))

    def test_current_rushees_with_filter(self):
        """ tests current rushees page with filter set """
        session = self.client.session
        session['rushee_filter'] = dict(name='first')
        session.save()
        path = reverse('rush:current_rushees')
        response = self.client.post(path)
        self.assertContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee1.pk))
        self.assertNotContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee2.pk))
        self.assertNotContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee3.pk))

    def test_current_rushees_with_cut(self):
        """ tests current rushees with cut filter set """
        session = self.client.session
        session['rushee_filter'] = dict(cut=True)
        session.save()
        path = reverse('rush:current_rushees')
        response = self.client.post(path)
        self.assertContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee1.pk))
        self.assertContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee2.pk))
        self.assertContains(response, "<tr onclick=\"window.location='rushee" + str(self.rushee3.pk))


class VotingTestCase(TenantTestCase):
    """ tests voting functions """
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.rushee = Rushee.objects.create(name="test_rushee", voting_open=True)
        self.user = User.objects.create(username="test_user", is_staff=True, is_superuser=True)
        self.client.force_login(self.user)

    def test_vote_function_y(self):
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        path = reverse('rush:vote', kwargs=dict(rushee_id=self.rushee.pk, value='y'))
        self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.rushee.refresh_from_db()
        self.assertEqual(self.rushee.y, 1)
        
    def test_vote_function_n(self):
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        path = reverse('rush:vote', kwargs=dict(rushee_id=self.rushee.pk, value='n'))
        self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.rushee.refresh_from_db()
        self.assertEqual(self.rushee.n, 1)
    
    def test_vote_function_a(self):
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        path = reverse('rush:vote', kwargs=dict(rushee_id=self.rushee.pk, value='a'))
        self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.rushee.refresh_from_db()
        self.assertEqual(self.rushee.a, 1)
    
    def test_vote_function_b(self):
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        path = reverse('rush:vote', kwargs=dict(rushee_id=self.rushee.pk, value='b'))
        self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.rushee.refresh_from_db()
        self.assertEqual(self.rushee.b, 1)
        self.assertTrue(self.rushee.blackball_list.get(username='test_user'))

    def test_voting_not_open(self):
        self.rushee.voting_open = False
        self.rushee.save()
        referer = reverse('rush:rushee', kwargs=dict(num=self.rushee.pk))
        path = reverse('rush:vote', kwargs=dict(rushee_id=self.rushee.pk, value='y'))
        response = self.client.post(path, HTTP_REFERER=referer, follow=True)
        self.assertContains(response, "Vote was not cast, because voting is not open.  Voting must be opened by an admin before votes will be recorded.")

    def test_push_rushee(self):
        path = reverse('rush:push', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(path, follow=True)
        self.rushee.refresh_from_db()
        self.assertEqual(self.rushee.round, 2)

    def test_push_rushee_with_next(self):
        """ tests pushing rushee when next rushee exists """
        Rushee.objects.create(name="test_rushee_2")
        path = reverse('rush:push', kwargs=dict(rushee_id=self.rushee.pk))
        response = self.client.post(path, follow=True)
        self.assertContains(response, '<h1 class="display-4">test_rushee_2</h1>')
        
    def test_cut_rushee(self):
        path = reverse('rush:cut', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(path, follow=True)
        self.rushee.refresh_from_db()
        self.assertTrue(self.rushee.cut)
        
    def test_cut_rushee_with_next(self):
        """ tests cutting rushee when next rushee exists """
        Rushee.objects.create(name="test_rushee_2")
        path = reverse('rush:cut', kwargs=dict(rushee_id=self.rushee.pk))
        response = self.client.post(path, follow=True)
        self.assertContains(response, '<h1 class="display-4">test_rushee_2</h1>')

    def test_uncut_rushee(self):
        """ tests uncutting rushee """
        path = reverse('rush:cut', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(path, follow=True)
        self.rushee.refresh_from_db()
        uncut_path = reverse('rush:uncut', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(uncut_path, follow=True)
        self.rushee.refresh_from_db()
        self.assertFalse(self.rushee.cut)

    def test_votepage(self):
        self.rushee.voting_open = False
        self.rushee.save()
        path = reverse('rush:votepage', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(path, follow=True)
        self.rushee.refresh_from_db()
        self.assertTrue(self.rushee.voting_open)
        
    def test_results(self):
        path = reverse('rush:results', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(path)
        self.rushee.refresh_from_db()
        self.assertFalse(self.rushee.voting_open)
        
    def test_reset(self):
        self.rushee.y = 1
        self.rushee.n = 1
        self.rushee.save()
        path = reverse('rush:reset', kwargs=dict(rushee_id=self.rushee.pk))
        self.client.post(path)
        self.rushee.refresh_from_db()
        self.assertEqual(self.rushee.y, 0)
        self.assertEqual(self.rushee.n, 0)


