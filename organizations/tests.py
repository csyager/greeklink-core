from django.test import TestCase, Client as HttpClient
from .models import Client
from django.urls import reverse
from core import urls
from core.forms import OrganizationSelectForm
from tenant_schemas.test.cases import TenantTestCase
from tenant_schemas.test.client import TenantClient


# Create your tests here.
class CommunityLoginTestCase(TestCase):

    def setUp(self):
        self.http_client = HttpClient()
        self.public_client = Client.objects.create(name="public", schema_name="public", domain_url="localhost")
        self.test_client = Client.objects.create(name="test", schema_name="test", domain_url="test.localhost")

    # tests community selection page
    def test_community_login_dropdown(self):
        path = reverse('login')
        response = self.http_client.get(path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<option value="{self.test_client.domain_url}">')
        self.assertNotContains(response, f'<option value="some.url.not.present">')

    def test_community_login_valid_input(self):
        path = reverse('login')
        post_data = {
            'organization': self.test_client.domain_url
        }
        form = OrganizationSelectForm(post_data)
        self.assertTrue(form.is_valid())
        response = self.http_client.post(path, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_community_login_invalid_input(self):
        path = reverse('login')
        post_data = {
            'organization': "some.url.not.present"
        }
        form = OrganizationSelectForm(post_data)
        self.assertFalse(form.is_valid())
        response = self.http_client.post(path, post_data, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("some.url.not.present is not one of the available choices" in str(form.errors))
        response = self.http_client.post(path, post_data, follow=True, HTTP_REFERER=path)
        self.assertContains(response, "Select your organization")
