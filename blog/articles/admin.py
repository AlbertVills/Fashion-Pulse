from django.contrib import admin

from .models import (
    ArticleComment,
    Article,
    ContactMessage,
    GalleryPost,
    GalleryPostComment,
    GalleryPostLike,
    UserNotification,
    UserProfile,
)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'submitted_by', 'moderation_status', 'is_trending', 'published_at')
    list_filter = ('moderation_status', 'is_trending', 'published_at')
    search_fields = ('title', 'excerpt', 'content', 'author', 'submitted_by__username')
    prepopulated_fields = {'slug': ('title',)}
    actions = ('approve_articles', 'reject_articles')

    @admin.action(description='Approve selected articles and publish to Trend Reports')
    def approve_articles(self, request, queryset):
        updated = queryset.update(
            moderation_status=Article.ModerationStatus.APPROVED,
            is_trending=True,
        )
        self.message_user(request, f'{updated} article(s) approved and published.')

    @admin.action(description='Reject selected articles and keep hidden from Trend Reports')
    def reject_articles(self, request, queryset):
        updated = queryset.update(
            moderation_status=Article.ModerationStatus.REJECTED,
            is_trending=False,
        )
        self.message_user(request, f'{updated} article(s) rejected.')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'fashion_style')
    search_fields = ('user__username', 'user__email', 'fashion_style')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('created_at',)


@admin.register(GalleryPost)
class GalleryPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'submitted_by', 'is_visible', 'created_at')
    list_filter = ('category', 'is_visible', 'created_at')
    search_fields = ('title', 'submitted_by__username', 'submitted_by__email')


@admin.register(GalleryPostLike)
class GalleryPostLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'user__username')


@admin.register(GalleryPostComment)
class GalleryPostCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'user__username', 'text')


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'notification_type', 'gallery_post', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username', 'gallery_post__title')


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('article__title', 'user__username', 'text')
