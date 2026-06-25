from django.test import TestCase
from apps.conversations.models import Conversation, Message
from apps.conversations.services.lock_service import LockService
from apps.conversations.services.suggestion_engine import SuggestionEngine


class ConversationModelTest(TestCase):

    def setUp(self):
        self.conv = Conversation.objects.create(customer_name="John Doe", status="open")

    # Unit Test 1 — get_last_message()
    def test_get_last_message_returns_latest(self):
        Message.objects.create(conversation=self.conv, sender='customer', message='Hello')
        Message.objects.create(conversation=self.conv, sender='agent',    message='Hi there')
        self.assertEqual(self.conv.get_last_message(), 'Hi there')

    def test_get_last_message_returns_none_when_empty(self):
        self.assertIsNone(self.conv.get_last_message())


class LockServiceTest(TestCase):

    # Unit Test 2 — TTL calculation
    def test_calculate_ttl_returns_zero_for_unlocked(self):
        ttl = LockService.calculate_ttl(9999)
        self.assertEqual(ttl, 0)

    def test_acquire_sets_positive_ttl(self):
        LockService.acquire_lock(1, agent_id=1)
        ttl = LockService.calculate_ttl(1)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 300)


class SuggestionEngineTest(TestCase):

    # Unit Test 3 — keyword mapping
    def test_refund_keyword_returns_apology(self):
        result = SuggestionEngine.get_suggestion("I want a refund")
        self.assertIn("refund", result.lower())

    def test_unknown_message_returns_default(self):
        result = SuggestionEngine.get_suggestion("xyzzy gobbledygook")
        self.assertEqual(result, SuggestionEngine.DEFAULT_REPLY)

    def test_regex_rule_matches_broken(self):
        result = SuggestionEngine.get_suggestion("My device is broken")
        self.assertIn("issue", result.lower())