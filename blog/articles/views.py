from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.urls import reverse_lazy

from .forms import ArticleCreateForm, ContactForm, GalleryPostForm, SignUpForm, UserAccountForm, UserProfileForm
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


class AdminAwareLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, 'You are now logged in.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

    def get_success_url(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return reverse_lazy('admin:index')
        return reverse_lazy('home')


def article_list(request):
    trending_stories = [
        {
            'image': 'https://images.unsplash.com/photo-1464863979621-258859e62245?auto=format&fit=crop&w=900&q=80',
            'category': 'Trend Report',
            'title': 'Streetwear Tailoring Sets the New Luxury Standard',
            'excerpt': 'Sharp structure meets relaxed ease as formalwear adapts to daily city movement.',
            'author': 'Nadia Brooks',
            'date': 'March 2, 2026',
        },
        {
            'image': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80',
            'category': 'Color Forecast',
            'title': 'Earth-Toned Minimalism Dominates Global Capsules',
            'excerpt': 'Clay, stone, and olive palettes are replacing colder neutrals in premium wardrobes.',
            'author': 'Luca Rivera',
            'date': 'March 1, 2026',
        },
        {
            'image': 'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80',
            'category': 'Runway Analysis',
            'title': 'Denim Layering Returns with Precision Cuts',
            'excerpt': 'Double-denim styling evolves through sculpted silhouettes and clean finishings.',
            'author': 'Anya Cho',
            'date': 'February 28, 2026',
        },
        {
            'image': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=80',
            'category': 'Industry Watch',
            'title': 'Athleisure 2.0 Rewrites Smart-Casual Dress Codes',
            'excerpt': 'Performance fabrics now lead office-ready styling as hybrid work reshapes demand.',
            'author': 'Maya Lin',
            'date': 'February 27, 2026',
        },
        {
            'image': 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80',
            'category': 'Street Style',
            'title': 'Vintage Accessories Power the Season’s Signature Looks',
            'excerpt': 'Structured handbags and statement eyewear create high-impact finishings.',
            'author': 'Noah Ellis',
            'date': 'February 26, 2026',
        },
        {
            'image': 'https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?auto=format&fit=crop&w=900&q=80',
            'category': 'Editorial',
            'title': 'Minimalist Power Dressing Becomes a Daily Uniform',
            'excerpt': 'Confident tailoring and disciplined palettes are defining modern authority.',
            'author': 'Imani Hart',
            'date': 'February 25, 2026',
        },
    ]

    gallery_posts = (
        GalleryPost.objects.filter(is_visible=True)
        .select_related('submitted_by')
        .prefetch_related('comments__user')
        .annotate(like_count=Count('likes', distinct=True), comment_count=Count('comments', distinct=True))
    )

    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(
            GalleryPostLike.objects.filter(user=request.user, post__in=gallery_posts)
            .values_list('post_id', flat=True)
        )

    return render(
        request,
        'index.html',
        {
            'trending_stories': trending_stories,
            'gallery_posts': gallery_posts,
            'liked_post_ids': liked_post_ids,
        },
    )


@login_required
def create_gallery_post(request):
    if request.method == 'POST':
        form = GalleryPostForm(request.POST, request.FILES)
        if form.is_valid():
            gallery_post = form.save(commit=False)
            gallery_post.submitted_by = request.user
            gallery_post.save()
            messages.success(request, 'Your photo was posted to the gallery.')
            return redirect('home')
    else:
        form = GalleryPostForm()

    return render(request, 'gallery_post_form.html', {'form': form})


@login_required
def toggle_gallery_heart(request, post_id):
    if request.method != 'POST':
        return redirect('home')

    post = get_object_or_404(GalleryPost, id=post_id, is_visible=True)
    like, created = GalleryPostLike.objects.get_or_create(post=post, user=request.user)

    if created:
        if post.submitted_by_id != request.user.id:
            UserNotification.objects.create(
                recipient=post.submitted_by,
                actor=request.user,
                notification_type=UserNotification.NotificationType.GALLERY_LIKE,
                gallery_post=post,
            )
    else:
        like.delete()

    return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")


@login_required
def add_gallery_comment(request, post_id):
    if request.method != 'POST':
        return redirect('home')

    post = get_object_or_404(GalleryPost, id=post_id, is_visible=True)
    text = request.POST.get('comment', '').strip()
    if text:
        comment = GalleryPostComment.objects.create(post=post, user=request.user, text=text[:300])
        if post.submitted_by_id != request.user.id:
            UserNotification.objects.create(
                recipient=post.submitted_by,
                actor=request.user,
                notification_type=UserNotification.NotificationType.GALLERY_COMMENT,
                gallery_post=post,
                comment=comment,
            )

    return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")


@login_required
def delete_gallery_comment(request, comment_id):
    if request.method != 'POST':
        return redirect('home')

    comment = get_object_or_404(GalleryPostComment.objects.select_related('post'), id=comment_id)
    post = comment.post
    can_delete = request.user.id == comment.user_id or request.user.id == post.submitted_by_id

    if not can_delete:
        messages.error(request, 'You are not allowed to delete this comment.')
        return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")

    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")


@login_required
def delete_gallery_post(request, post_id):
    if request.method != 'POST':
        return redirect('home')

    post = get_object_or_404(GalleryPost, id=post_id)
    if post.submitted_by_id != request.user.id:
        messages.error(request, 'You can only delete your own photo.')
        return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")

    post.delete()
    messages.success(request, 'Your photo was deleted.')
    return redirect('home')


def trends_page(request):
    trend_reports = Article.objects.filter(
        is_trending=True,
        moderation_status=Article.ModerationStatus.APPROVED,
    ).select_related('submitted_by__profile')
    return render(request, 'trends.html', {'trend_reports': trend_reports})


def full_article_page(request):
    return render(request, 'article_detail.html')


@login_required
def create_trend_article(request):
    if request.method == 'POST':
        form = ArticleCreateForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.is_trending = False
            article.moderation_status = Article.ModerationStatus.PENDING
            article.author = request.user.get_full_name() or request.user.username
            article.submitted_by = request.user

            base_slug = slugify(article.title)[:210] or 'trend-report'
            slug = base_slug
            suffix = 2
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            article.slug = slug

            article.save()
            messages.success(request, 'Your article was submitted to admin for review. It will appear in Trend Reports after approval.')
            return redirect('trends')
    else:
        form = ArticleCreateForm()

    return render(request, 'trend_article_form.html', {'form': form})


def trend_article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related('submitted_by__profile'),
        slug=slug,
        is_trending=True,
        moderation_status=Article.ModerationStatus.APPROVED,
    )
    article_comments = article.comments.select_related('user')[:20]
    return render(
        request,
        'trend_article_detail.html',
        {
            'article': article,
            'article_comments': article_comments,
        },
    )


@login_required
def add_article_comment(request, slug):
    if request.method != 'POST':
        return redirect('trends')

    article = get_object_or_404(
        Article,
        slug=slug,
        is_trending=True,
        moderation_status=Article.ModerationStatus.APPROVED,
    )
    text = request.POST.get('comment', '').strip()
    if text:
        ArticleComment.objects.create(article=article, user=request.user, text=text[:500])
    return redirect(f"{reverse_lazy('trend-article-detail', kwargs={'slug': article.slug})}#article-comments")


@login_required
def delete_article_comment(request, comment_id):
    if request.method != 'POST':
        return redirect('trends')

    comment = get_object_or_404(ArticleComment.objects.select_related('article'), id=comment_id)
    article = comment.article
    can_delete = request.user.id == comment.user_id or request.user.id == article.submitted_by_id
    if not can_delete:
        messages.error(request, 'You are not allowed to delete this comment.')
        return redirect(f"{reverse_lazy('trend-article-detail', kwargs={'slug': article.slug})}#article-comments")

    comment.delete()
    messages.success(request, 'Comment deleted.')
    return redirect(f"{reverse_lazy('trend-article-detail', kwargs={'slug': article.slug})}#article-comments")


def insights_page(request):
    insight_posts = [
        {
            'category': 'Fashion Psychology',
            'title': 'Why Structured Clothing Signals Confidence',
            'excerpt': 'How visual discipline in outfits influences self-perception and social response.',
            'image': '/static/images/pyschology.jpg',
        },
        {
            'category': 'Cultural Analysis',
            'title': 'Minimalism as a Post-Excess Cultural Reset',
            'excerpt': 'A wider cultural pivot toward utility, longevity, and quieter status symbols.',
            'image': '/static/images/minimalism.jpg',
        },
        {
            'category': 'Industry Commentary',
            'title': 'What Buyers Want from 2026 Collections',
            'excerpt': 'Retail buyers prioritize adaptable pieces with strong cross-season relevance.',
            'image': '/static/images/buyers1.jpg',
        },
        {
            'category': 'Sustainability',
            'title': 'Durability Is the New Luxury Metric',
            'excerpt': 'Longevity and repairability now shape premium product value and brand trust.',
            'image': '/static/images/sustainability.jpg',
        },
    ]
    return render(request, 'insights.html', {'insight_posts': insight_posts})


def about_page(request):
    return render(request, 'about.html')


def contact_page(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(**form.cleaned_data)
            messages.success(request, 'Your message was sent successfully.')
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if 'remove_profile_image' in request.POST:
            if profile.profile_image:
                profile.profile_image.delete(save=False)
                profile.profile_image = ''
                profile.save(update_fields=['profile_image'])
                messages.success(request, 'Profile image removed.')
            return redirect('profile')

        account_form = UserAccountForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if account_form.is_valid() and profile_form.is_valid():
            account_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
    else:
        account_form = UserAccountForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    progress_items = [
        {'label': 'Setup account', 'done': bool(request.user.username and request.user.email)},
        {
            'label': 'Personal info',
            'done': bool(
                request.user.first_name
                and request.user.last_name
                and profile.phone_number
            ),
        },
        {'label': 'Location', 'done': bool(profile.location)},
        {'label': 'Biography', 'done': bool(profile.about_self.strip())},
        {'label': 'Fashion style', 'done': bool(profile.fashion_style)},
        {'label': 'Age', 'done': bool(profile.age)},
        {'label': 'Photo', 'done': bool(profile.profile_image)},
    ]
    completed_count = sum(1 for item in progress_items if item['done'])
    completion_percent = int((completed_count / len(progress_items)) * 100)
    notifications = UserNotification.objects.filter(recipient=request.user).select_related('actor', 'gallery_post')[:20]

    return render(
        request,
        'profile.html',
        {
            'account_form': account_form,
            'profile_form': profile_form,
            'progress_items': progress_items,
            'completion_percent': completion_percent,
            'notifications': notifications,
        },
    )
