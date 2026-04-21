import re
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


def validate_phone(value):
    """Faqat +998XXXXXXXXX formati qabul qilinadi."""
    if not re.match(r'^\+998\d{9}$', value):
        raise ValidationError("Telefon raqam +998XXXXXXXXX formatida bo'lishi kerak.")


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqam majburiy.")
        validate_phone(phone)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(
        max_length=13,
        unique=True,
        validators=[validate_phone],
        help_text="+998XXXXXXXXX formatida",
    )
    full_name = models.CharField(max_length=150, help_text="Ism va familiya")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} ({self.phone})'

    @property
    def first_name(self):
        """Home ekrandagi 'Salom, Azim!' uchun — ism (birinchi so'z)."""
        return self.full_name.split()[0] if self.full_name else ''
