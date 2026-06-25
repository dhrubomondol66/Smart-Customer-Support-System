from django.db import models
from django.conf import settings


class Conversation(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pending', 'Pending'),
    ]
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]

    customer_name = models.CharField(max_length=200)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    sentiment     = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_name} ({self.status})"

    def get_last_message(self):
        """Returns the text of the most recent message, or None."""
        last = self.messages.order_by('-timestamp', '-id').first()
        return last.message if last else None

    def is_locked(self):
        """Check if this conversation has an active Redis lock."""
        from .services.lock_service import LockService
        return LockService.get_lock_owner(self.id) is not None


class Message(models.Model):
    SENDER_CHOICES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender    = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message   = models.TextField()
    agent     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True  # null for customer messages
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.sender}] {self.message[:50]}"