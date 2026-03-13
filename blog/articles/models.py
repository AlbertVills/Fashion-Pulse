from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Article(models.Model):
    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.CharField(max_length=300)
    content = models.TextField()
    author = models.CharField(max_length=120, default='Fashion Desk')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_articles',
    )
    is_trending = models.BooleanField(default=True)
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.APPROVED,
    )
    published_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    @property
    def author_profile_image_url(self):
        if not self.submitted_by:
            return ''
        try:
            profile = self.submitted_by.profile
        except ObjectDoesNotExist:
            return ''

        if not profile.profile_image:
            return ''
        return profile.profile_image.url


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


class GalleryPost(models.Model):
    class Category(models.TextChoices):
        STREET = 'street', 'Street Style'
        MODERN = 'modern', 'Modern Style'
        MINIMAL = 'minimal', 'Minimal Style'
        VINTAGE = 'vintage', 'Vintage Style'
        OTHER = 'other', 'Other'

    title = models.CharField(max_length=140)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.STREET)
    image = models.ImageField(upload_to='gallery/')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gallery_posts',
    )
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class GalleryPostLike(models.Model):
    post = models.ForeignKey(GalleryPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gallery_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_gallery_post_like'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} liked {self.post}"


class GalleryPostComment(models.Model):
    post = models.ForeignKey(GalleryPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gallery_comments')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"


class UserNotification(models.Model):
    class NotificationType(models.TextChoices):
        GALLERY_LIKE = 'gallery_like', 'Gallery Like'
        GALLERY_COMMENT = 'gallery_comment', 'Gallery Comment'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    gallery_post = models.ForeignKey(
        GalleryPost,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    comment = models.ForeignKey(
        GalleryPostComment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def message(self):
        actor_name = self.actor.get_full_name() or self.actor.username
        if self.notification_type == self.NotificationType.GALLERY_LIKE:
            return f"{actor_name} hearted your photo \"{self.gallery_post.title}\"."
        if self.notification_type == self.NotificationType.GALLERY_COMMENT and self.comment:
            return f"{actor_name} commented on your photo \"{self.gallery_post.title}\": {self.comment.text}"
        return f"{actor_name} interacted with your photo."

    def __str__(self):
        return f"Notification for {self.recipient}"


class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='article_comments')
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.article}"


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
