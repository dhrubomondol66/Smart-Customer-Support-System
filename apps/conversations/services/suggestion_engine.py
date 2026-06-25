import re
from typing import Optional


class SuggestionEngine:
    """
    Rule-based mock AI reply suggestion engine.
    No external API calls — uses keyword mapping + regex patterns.
    Easily extensible: add new rules to KEYWORD_MAP or REGEX_RULES.
    """

    # Priority 1 — exact keyword map (checked first)
    KEYWORD_MAP = {
        'refund':    "We are sorry for the inconvenience. We have initiated your refund and it will reflect within 5–7 business days.",
        'cancel':    "We understand you'd like to cancel. Please share your order ID and we'll process the cancellation immediately.",
        'shipping':  "Your order is on its way! You can track it using the tracking link sent to your registered email.",
        'delay':     "We apologize for the delay. Our team is actively working to resolve this and will update you shortly.",
        'password':  "To reset your password, click Forgot Password on the login page and follow the instructions.",
        'account':   "For account-related concerns, please verify your registered email and we'll assist you right away.",
        'payment':   "We're sorry you're facing a payment issue. Please check your bank details or try an alternate payment method.",
        'damaged':   "We sincerely apologize for receiving a damaged item. Please share a photo and your order ID.",
        'wrong':     "We're sorry you received the wrong item. Please share your order ID and a photo.",
        'discount':  "We currently have ongoing promotions! Please check our offers page for exclusive deals.",
        'hello':     "Hello! How can we assist you today?",
        'hi':        "Hi there! How can we help you?",
        'help':      "We are here to help! Please describe your issue.",
        'order':     "Please share your order ID and we will look into it.",
        'late':      "We apologize for the inconvenience caused by the delay.",
        'angry':     "We sincerely apologize for your experience.",
        'waiting':   "We appreciate your patience, we are working on it.",
        'complaint': "We take all complaints seriously and will resolve this.",
    }

    # Priority 2 — regex patterns for more complex phrases
    REGEX_RULES = [
        (
            re.compile(r'(not working|doesn\'t work|broken|issue|problem)', re.IGNORECASE),
            "We're sorry to hear you're experiencing an issue. "
            "Could you describe the problem in more detail so we can assist you faster?"
        ),
        (
            re.compile(r'(talk to|speak with|connect me|human|agent|representative)', re.IGNORECASE),
            "Connecting you to a senior support agent right away. "
            "Please hold for a moment."
        ),
        (
            re.compile(r'(how long|when will|estimated time|eta)', re.IGNORECASE),
            "Our typical response time is 24–48 hours. "
            "We'll make sure to prioritize your case."
        ),
        (
            re.compile(r'(thank|thanks|appreciate|grateful)', re.IGNORECASE),
            "You're welcome! Is there anything else we can help you with today?"
        ),
    ]

    # Default fallback
    DEFAULT_REPLY = (
        "Thank you for reaching out! "
        "Our support team will review your message and get back to you shortly."
    )

    @classmethod
    def get_suggestion(cls, message: str) -> str:
        """
        Main entry point. Returns best matching suggestion for the message.
        """
        message_lower = message.lower()

        # Check keyword map first
        for keyword, reply in cls.KEYWORD_MAP.items():
            if keyword in message_lower:
                return reply

        # Check regex patterns
        for pattern, reply in cls.REGEX_RULES:
            if pattern.search(message):
                return reply

        return cls.DEFAULT_REPLY

    @classmethod
    def add_rule(cls, keyword: str, reply: str):
        """
        Dynamically add new keyword rules at runtime.
        Demonstrates extensibility.
        """
        cls.KEYWORD_MAP[keyword] = reply