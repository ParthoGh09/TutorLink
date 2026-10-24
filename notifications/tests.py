from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from notifications.models import Notification, NotificationType


class NotificationsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='ayesha_rahman',
            email='ayesha.rahman@gmail.com',
            password='password123',
            first_name='Ayesha',
            last_name='Rahman'
        )
        self.noti1 = Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.MATCH,
            title='New 95% match found',
            description='Tanvir Hasan matches your Math post.',
            is_read=False
        )
        self.noti2 = Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.APPLICATION,
            title='Nusrat Jahan applied to your post',
            description='Review her profile and shortlist.',
            is_read=False
        )

    def test_notification_list_get(self):
        """Test notifications list page renders with unread counts."""
        response = self.client.get(reverse('notifications:notification_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New 95% match found')
        self.assertContains(response, '2 Unread')

    def test_notification_filter(self):
        """Test filtering by NotificationType."""
        response = self.client.get(reverse('notifications:notification_list') + '?filter=MATCH')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New 95% match found')
        self.assertNotContains(response, 'Nusrat Jahan applied')

    def test_mark_as_read_ajax(self):
        """Test marking a single notification as read via AJAX."""
        response = self.client.get(
            reverse('notifications:mark_as_read', args=[self.noti1.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.noti1.refresh_from_db()
        self.assertTrue(self.noti1.is_read)

    def test_mark_all_as_read_ajax(self):
        """Test marking all notifications as read via AJAX."""
        response = self.client.post(
            reverse('notifications:mark_all_as_read'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        unread_count = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread_count, 0)
