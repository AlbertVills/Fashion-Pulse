from django.contrib import admin

from .forms import AdminArticleForm, AdminContactMessageForm, AdminUserProfileForm
from .models import Article, ContactMessage, UserProfile


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = AdminArticleForm
    list_display = ('title', 'author', 'is_trending', 'published_at')
    list_filter = ('is_trending', 'published_at')
    search_fields = ('title', 'excerpt', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = AdminUserProfileForm
    list_display = ('user', 'age', 'fashion_style')
    search_fields = ('user__username', 'user__email', 'fashion_style')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    form = AdminContactMessageForm
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('created_at',)
