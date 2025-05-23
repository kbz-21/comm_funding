from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Campaign
import datetime

class CampaignTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        
        self.campaign_data = {
            'title': 'Test Campaign',
            'category': 'ACADEMIC',
            'description': 'Test Description',
            'goal_amount': 1000.00,
            'starting_date': datetime.date.today() + datetime.timedelta(days=1),
            'ending_date': datetime.date.today() + datetime.timedelta(days=10),
            'location': 'Test City',
            'image': 'test.jpg',  # Placeholder for file upload in API tests
            'document': 'test.pdf',  # Placeholder for file upload in API tests
        }

    def test_create_campaign_api(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('api_campaign_create'), self.campaign_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Campaign.objects.count(), 1)
        self.assertEqual(Campaign.objects.first().status, 'PENDING')

    def test_admin_review_api(self):
        self.client.login(username='admin', password='adminpass')
        campaign = Campaign.objects.create(
            **self.campaign_data,
            created_by=self.user,
            status='PENDING'
        )
        response = self.client.patch(
            reverse('api_admin_review', kwargs={'campaign_id': campaign.id}),
            {'status': 'APPROVED'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, 'APPROVED')

    def test_get_approved_campaigns(self):
        Campaign.objects.create(
            **self.campaign_data,
            created_by=self.user,
            status='APPROVED'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('api_campaigns'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'APPROVED')

# Create your tests here.
