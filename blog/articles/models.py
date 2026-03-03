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
