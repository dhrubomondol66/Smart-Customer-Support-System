from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class AgentManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Agent(AbstractUser):
    """
    Support agent account.
    Extends Django's default user — gives you
    email, password, is_active etc. for free.
    """
    username = None  # remove username, use email instead
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = AgentManager()

    def __str__(self):
        return self.email