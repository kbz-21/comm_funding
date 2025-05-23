from django.test import TestCase
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from .models import Video
import json

class VideoAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin', password='admin123', email='admin@example.com'
        )
        self.client.login(username='admin', password='admin123')

    def test_upload_video(self):
        video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"file_content",
            content_type="video/mp4"
        )
        response = self.client.post('/api/videos/', {
            'title': 'Test Video',
            'video_file': video_file
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['message'], 'Video uploaded successfully')
        self.assertEqual(response_data['data']['title'], 'Test Video')
        self.assertEqual(Video.objects.count(), 1)

    def test_upload_video_unauthorized(self):
        self.client.logout()  # Log out to simulate non-admin
        video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"file_content",
            content_type="video/mp4"
        )
        response = self.client.post('/api/videos/', {
            'title': 'Test Video',
            'video_file': video_file
        }, format='multipart')
        self.assertEqual(response.status_code, 403)  # Forbidden for non-admins

    def test_get_latest_video(self):
        video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"file_content",
            content_type="video/mp4"
        )
        Video.objects.create(title='Test Video', video_file=video_file)
        response = self.client.get('/api/videos/latest/')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['data']['title'], 'Test Video')
        self.assertIn('test_video.mp4', response_data['data']['video_file'])

    def test_get_latest_video_no_video(self):
        response = self.client.get('/api/videos/latest/')
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'No video available')
# Create your tests here.
