from celery import shared_task
import re


@shared_task
def analyze_sentiment(conversation_id: int, message_text: str):
    """
    Background task: compute mock sentiment from message text
    and update the conversation's sentiment field.
    Fires after agent sends a reply — does NOT block the HTTP response.
    """
    from .models import Conversation  # avoid circular import

    sentiment = _compute_sentiment(message_text)

    Conversation.objects.filter(id=conversation_id).update(sentiment=sentiment)

    return f"Conversation {conversation_id} sentiment → {sentiment}"


def _compute_sentiment(text: str) -> str:
    """
    Rule-based sentiment scorer.
    Returns 'positive', 'neutral', or 'negative'.
    """
    text_lower = text.lower()

    positive_words = [
        'thank', 'thanks', 'great', 'good', 'happy', 'resolved',
        'perfect', 'awesome', 'appreciate', 'helpful', 'excellent'
    ]
    negative_words = [
        'angry', 'terrible', 'horrible', 'worst', 'useless',
        'refund', 'cancel', 'damaged', 'broken', 'fraud',
        'disappointed', 'unacceptable', 'awful', 'pathetic'
    ]

    pos_score = sum(1 for w in positive_words if w in text_lower)
    neg_score = sum(1 for w in negative_words if w in text_lower)

    if pos_score > neg_score:
        return 'positive'
    elif neg_score > pos_score:
        return 'negative'
    else:
        return 'neutral'