from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from datetime import timedelta
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
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
    ]

    raw_gallery_category = request.GET.get('gallery_category', '').strip()
    selected_gallery_category = raw_gallery_category
    normalized_gallery_category = ''

    if raw_gallery_category:
        lowered_query = raw_gallery_category.lower()
        for value, label in GalleryPost.Category.choices:
            if lowered_query in {value.lower(), label.lower()}:
                normalized_gallery_category = value
                break

    gallery_posts = GalleryPost.objects.filter(is_visible=True)
    if normalized_gallery_category:
        gallery_posts = gallery_posts.filter(category=normalized_gallery_category)

    gallery_posts = (
        gallery_posts
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
            'selected_gallery_category': selected_gallery_category,
            'gallery_category_choices': GalleryPost.Category.choices,
            'gallery_filter_active': bool(raw_gallery_category),
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
    default_outfit_cards = [
        {
            'name': 'Neutral Layer Set',
            'category': 'modern',
            'description': 'Balanced tones and clean layers for daily polished looks.',
            'image': 'https://images.unsplash.com/photo-1464863979621-258859e62245?auto=format&fit=crop&w=900&q=80',
        },
        {
            'name': 'Oversized Street Fit',
            'category': 'street',
            'description': 'Relaxed shape with strong attitude for city styling.',
            'image': 'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=900&q=80',
        },
        {
            'name': 'Minimal Linen Combo',
            'category': 'minimal',
            'description': 'Lightweight fabric and soft structure for warm weather edits.',
            'image': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=80',
        },
        {
            'name': 'Soft Casual Essentials',
            'category': 'casual',
            'description': 'Comfort-first staples that still look refined and fresh.',
            'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80',
        },
    ]

    gallery_to_outfit_category = {
        GalleryPost.Category.MODERN: 'modern',
        GalleryPost.Category.STREET: 'street',
        GalleryPost.Category.MINIMAL: 'minimal',
        GalleryPost.Category.VINTAGE: 'casual',
        GalleryPost.Category.OTHER: 'casual',
    }

    raw_outfit_period = request.GET.get('outfit_period', '').strip().lower()
    selected_outfit_period = raw_outfit_period if raw_outfit_period in {'all', 'today', 'this_week', 'yesterday'} else 'all'

    gallery_outfit_cards = []
    latest_gallery_posts = GalleryPost.objects.filter(is_visible=True)
    today = timezone.localdate()
    if selected_outfit_period == 'today':
        latest_gallery_posts = latest_gallery_posts.filter(created_at__date=today)
    elif selected_outfit_period == 'yesterday':
        yesterday = today - timedelta(days=1)
        latest_gallery_posts = latest_gallery_posts.filter(created_at__date=yesterday)
    elif selected_outfit_period == 'this_week':
        week_start = today - timedelta(days=today.weekday())
        latest_gallery_posts = latest_gallery_posts.filter(created_at__date__gte=week_start, created_at__date__lte=today)

    latest_gallery_posts = latest_gallery_posts.select_related('submitted_by')[:8]

    for post in latest_gallery_posts:
        if not post.image:
            continue

        submitter_name = post.submitted_by.get_full_name() or post.submitted_by.username
        gallery_outfit_cards.append(
            {
                'name': post.title,
                'category': gallery_to_outfit_category.get(post.category, 'casual'),
                'description': f"{post.get_category_display()} by {submitter_name} from the Home gallery.",
                'image': post.image.url,
                'owner_username': post.submitted_by.username,
            }
        )

    # Prioritize real gallery uploads in Latest Collection, then backfill with curated defaults.
    outfit_cards = gallery_outfit_cards[:8]
    if selected_outfit_period == 'all' and len(outfit_cards) < 4:
        outfit_cards.extend(default_outfit_cards[: 4 - len(outfit_cards)])
    catalogue_items = [
        {
            'label': 'Blue',
            'image': 'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'White',
            'image': 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'Black',
            'image': 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1475180098004-ca77a66827be?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'Beige',
            'image': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'Shirt',
            'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'Pants',
            'image': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'Skirt',
            'image': 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1554412933-514a83d2f3c8?auto=format&fit=crop&w=800&q=80',
        },
        {
            'label': 'Style',
            'image': 'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=800&q=80',
            'hover_image': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80',
        },
    ]
    popular_feature = {
        'title': 'Discover A/W Product Picks',
        'excerpt': 'Fashion desk picks with strong shape, cleaner silhouettes, and practical layering for daily wear.',
        'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1200&q=80',
    }
    popular_outfits = [
        {
            'title': 'Patterned Knit Jacket',
            'tag': 'Article Pick',
            'image': 'https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?auto=format&fit=crop&w=700&q=80',
        },
        {
            'title': 'Pastel Office Sweat',
            'tag': 'Street Edit',
            'image': 'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=700&q=80',
        },
        {
            'title': 'Urban Black Shoulder Bag',
            'tag': 'Accessory',
            'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80',
        },
        {
            'title': 'Neutral Cotton Set',
            'tag': 'Minimal',
            'image': 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?auto=format&fit=crop&w=700&q=80',
        },
        {
            'title': 'Relaxed Beige Blazer',
            'tag': 'Runway Note',
            'image': 'https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?auto=format&fit=crop&w=700&q=80',
        },
        {
            'title': 'Urban Soft Tee Dress',
            'tag': 'Fresh Drop',
            'image': 'https://images.unsplash.com/photo-1464863979621-258859e62245?auto=format&fit=crop&w=700&q=80',
        },
    ]
    return render(
        request,
        'insights.html',
        {
            'outfit_cards': outfit_cards,
            'selected_outfit_period': selected_outfit_period,
            'outfit_period_filter_active': selected_outfit_period != 'all',
            'catalogue_items': catalogue_items,
            'popular_feature': popular_feature,
            'popular_outfits': popular_outfits,
        },
    )


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


def gallery_page(request):
    raw_gallery_category = request.GET.get('gallery_category', '').strip()
    selected_gallery_category = raw_gallery_category
    normalized_gallery_category = ''

    if raw_gallery_category:
        lowered_query = raw_gallery_category.lower()
        for value, label in GalleryPost.Category.choices:
            if lowered_query in {value.lower(), label.lower()}:
                normalized_gallery_category = value
                break

    gallery_posts = GalleryPost.objects.filter(is_visible=True)
    if normalized_gallery_category:
        gallery_posts = gallery_posts.filter(category=normalized_gallery_category)

    gallery_posts = (
        gallery_posts
        .select_related('submitted_by', 'submitted_by__profile')
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
        'gallery.html',
        {
            'gallery_posts': gallery_posts,
            'liked_post_ids': liked_post_ids,
            'selected_gallery_category': selected_gallery_category,
            'gallery_category_choices': GalleryPost.Category.choices,
            'gallery_filter_active': bool(raw_gallery_category),
        },
    )


def user_gallery_page(request, username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    owner = get_object_or_404(User, username=username)
    try:
        owner_profile = owner.profile
    except UserProfile.DoesNotExist:
        owner_profile = None

    posts = (
        GalleryPost.objects.filter(submitted_by=owner, is_visible=True)
        .prefetch_related('comments__user')
        .annotate(like_count=Count('likes', distinct=True), comment_count=Count('comments', distinct=True))
    )

    trend_articles = Article.objects.filter(submitted_by=owner)

    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(
            GalleryPostLike.objects.filter(user=request.user, post__in=posts)
            .values_list('post_id', flat=True)
        )

    return render(
        request,
        'user_gallery.html',
        {
            'owner': owner,
            'owner_profile': owner_profile,
            'posts': posts,
            'liked_post_ids': liked_post_ids,
            'trend_articles': trend_articles,
        },
    )
