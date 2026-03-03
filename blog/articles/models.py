from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.CharField(max_length=300)
    content = models.TextField()
    author = models.CharField(max_length=120, default='Fashion Desk')
    is_trending = models.BooleanField(default=True)
    published_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.email})"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(120)],
    )
    fashion_style = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=120, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    about_self = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} profile"


def _create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


models.signals.post_save.connect(_create_user_profile, sender=get_user_model())
