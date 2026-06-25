from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import Agent
from apps.conversations.models import Conversation
from apps.conversations.services.lock_service import LockService
from unittest.mock import patch


class AuthenticationTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.agent  = Agent.objects.create_user(email='test@test.com', password='pass123')
        self.conv   = Conversation.objects.create(customer_name='Jane', status='open')

    # Integration Test 1 — JWT header validation
    def test_request_without_jwt_returns_401(self):
        response = self.client.get('/conversations/')
        self.assertEqual(response.status_code, 401)

    def test_request_with_jwt_returns_200(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get('/conversations/')
        self.assertEqual(response.status_code, 200)

    def test_search_filter_works(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get('/conversations/?search=Jane')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['customer_name'], 'Jane')

    def test_status_filter_works(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get('/conversations/?status=open')
        self.assertEqual(response.status_code, 200)


class LockIntegrationTest(TestCase):

    def setUp(self):
        self.client  = APIClient()
        self.agent1  = Agent.objects.create_user(email='agent1@test.com', password='pass')
        self.agent2  = Agent.objects.create_user(email='agent2@test.com', password='pass')
        self.conv    = Conversation.objects.create(customer_name='Bob', status='open')

    # Integration Test 2 — lock blocks other agent
    @patch('apps.conversations.tasks.analyze_sentiment.delay')
    def test_locked_conversation_blocks_other_agent(self, mock_task):
        # Agent 1 acquires lock
        LockService.acquire_lock(self.conv.id, self.agent1.id)

        # Agent 2 tries to send a message
        self.client.force_authenticate(user=self.agent2)
        response = self.client.post(
            f'/conversations/{self.conv.id}/messages/send/',
            {'message': 'Hello from agent 2'}
        )
        self.assertEqual(response.status_code, 423)
        self.assertIn('locked', response.data['error'].lower())

    @patch('apps.conversations.tasks.analyze_sentiment.delay')
    def test_celery_task_triggered_on_message_send(self, mock_task):
        self.client.force_authenticate(user=self.agent1)
        # Agent 1 owns the lock
        LockService.acquire_lock(self.conv.id, self.agent1.id)
        self.client.post(
            f'/conversations/{self.conv.id}/messages/send/',
            {'message': 'Test message'}
        )
        # Verify Celery task was called
        mock_task.assert_called_once()