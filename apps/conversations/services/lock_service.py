import django_redis
from django.core.cache import cache

LOCK_TTL_SECONDS = 300  # 5 minutes


class LockService:

    @staticmethod
    def _key(conversation_id: int) -> str:
        return f"conversation_lock:{conversation_id}"

    @staticmethod
    def acquire_lock(conversation_id: int, agent_id: int) -> bool:
        """
        Try to acquire lock for this conversation.
        Uses SET NX (set if not exists) — atomic, no race condition.
        Returns True if lock acquired, False if already locked by someone else.
        """
        key = LockService._key(conversation_id)
        # cache.add() returns True only if key did NOT exist → atomic NX
        return cache.add(key, str(agent_id), timeout=LOCK_TTL_SECONDS)

    @staticmethod
    def release_lock(conversation_id: int, agent_id: int) -> bool:
        """
        Release lock only if this agent owns it.
        Returns True if released, False if not owner.
        """
        key = LockService._key(conversation_id)
        owner = cache.get(key)
        if owner == str(agent_id):
            cache.delete(key)
            return True
        return False

    @staticmethod
    def get_lock_owner(conversation_id: int):
        """Returns agent_id string who holds the lock, or None."""
        return cache.get(LockService._key(conversation_id))

    @staticmethod
    def calculate_ttl(conversation_id: int) -> int:
        """
        Returns remaining TTL in seconds.
        Used in tests and lock status endpoint.
        """
        key = LockService._key(conversation_id)
        # django-redis exposes ttl via cache.ttl()
        try:
            ttl = cache.ttl(key)
            return ttl if ttl and ttl > 0 else 0
        except Exception:
            return 0

    @staticmethod
    def force_release(conversation_id: int):
        """Admin-only force release regardless of owner."""
        cache.delete(LockService._key(conversation_id))