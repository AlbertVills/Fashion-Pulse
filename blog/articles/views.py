import os
import secrets
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from datetime import timedelta
from django.conf import settings as django_settings
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse_lazy
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import (
    ArticleCreateForm,
    ContactForm,
    GalleryPostForm,
    PasswordResetCodeConfirmForm,
    PasswordResetCodeRequestForm,
    SignUpForm,
    UserAccountForm,
    UserProfileForm,
)
from .models import (
    ArticleComment,
    Article,
    ContactMessage,
    EmailVerification,
    GalleryPost,
    GalleryPostComment,
    GalleryPostLike,
    PasswordResetCode,
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


def _ensure_email_settings_loaded():
    """Load SMTP credentials from .env at runtime for long-running dev servers."""
    if django_settings.EMAIL_HOST_USER and django_settings.EMAIL_HOST_PASSWORD:
        return

    env_path = Path(django_settings.BASE_DIR).parent / '.env'
    if not env_path.exists():
        return

    env_values = {}
    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        env_values[key.strip()] = value.strip().strip('"').strip("'")

    host_user = env_values.get('EMAIL_HOST_USER', '')
    host_password = env_values.get('EMAIL_HOST_PASSWORD', '')
    app_base_url = env_values.get('APP_BASE_URL', '').strip().rstrip('/')
    if host_user:
        os.environ['EMAIL_HOST_USER'] = host_user
        django_settings.EMAIL_HOST_USER = host_user
        django_settings.DEFAULT_FROM_EMAIL = host_user
    if host_password:
        os.environ['EMAIL_HOST_PASSWORD'] = host_password
        django_settings.EMAIL_HOST_PASSWORD = host_password
    if app_base_url:
        os.environ['APP_BASE_URL'] = app_base_url
        django_settings.APP_BASE_URL = app_base_url


def _build_public_url(request, path):
    base_url = (getattr(django_settings, 'APP_BASE_URL', '') or '').strip().rstrip('/')
    if base_url:
        path_str = str(path)
        if not path_str.startswith('/'):
            path_str = f'/{path_str}'
        return f'{base_url}{path_str}'
    return request.build_absolute_uri(path)


def password_reset_request_code(request):
    if request.method == 'POST':
        form = PasswordResetCodeRequestForm(request.POST)
        if form.is_valid():
            _ensure_email_settings_loaded()
            if not django_settings.EMAIL_HOST_USER or not django_settings.EMAIL_HOST_PASSWORD:
                form.add_error(None, 'Password reset email is not configured yet. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env.')
                return render(request, 'registration/password_reset_form.html', {'form': form})

            email = form.cleaned_data['email'].strip().lower()
            User = get_user_model()
            user = User.objects.filter(email__iexact=email, is_active=True).first()

            if user:
                reset_code = f'{secrets.randbelow(1000000):06d}'
                PasswordResetCode.objects.update_or_create(
                    user=user,
                    defaults={'reset_code': reset_code},
                )

                from django.core.mail import send_mail
                try:
                    send_mail(
                        subject='Your FashionPulse password reset code',
                        message=(
                            f'Hi {user.username},\n\n'
                            f'Your FashionPulse password reset code is: {reset_code}\n\n'
                            f'Enter this code on the reset page to create a new password.\n\n'
                            f'If you did not request this, ignore this email.'
                        ),
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception as exc:
                    form.add_error(None, f'Unable to send password reset code: {exc}')
                    return render(request, 'registration/password_reset_form.html', {'form': form})

            return render(request, 'registration/password_reset_done.html', {'email': email})
    else:
        form = PasswordResetCodeRequestForm()

    return render(request, 'registration/password_reset_form.html', {'form': form})


def password_reset_code_confirm(request):
    initial_email = request.GET.get('email', '').strip().lower()

    if request.method == 'POST':
        form = PasswordResetCodeConfirmForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            code = form.cleaned_data['code']

            User = get_user_model()
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if not user:
                form.add_error(None, 'Invalid email or reset code.')
                return render(request, 'registration/password_reset_confirm.html', {'form': form})

            reset = PasswordResetCode.objects.filter(user=user).first()
            if not reset or reset.reset_code != code:
                form.add_error('code', 'Invalid reset code.')
                return render(request, 'registration/password_reset_confirm.html', {'form': form})

            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            reset.delete()

            return redirect('password_reset_complete')
    else:
        form = PasswordResetCodeConfirmForm(initial={'email': initial_email})

    return render(request, 'registration/password_reset_confirm.html', {'form': form})


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
        if lowered_query not in {'all', 'all category', 'all categories'}:
            for value, label in GalleryPost.Category.choices:
                if lowered_query in {value.lower(), label.lower()}:
                    normalized_gallery_category = value
                    break
        else:
            selected_gallery_category = ''

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

    context = {
        'trending_stories': trending_stories,
        'gallery_posts': gallery_posts,
        'liked_post_ids': liked_post_ids,
        'selected_gallery_category': selected_gallery_category,
        'gallery_category_choices': GalleryPost.Category.choices,
        'gallery_filter_active': bool(normalized_gallery_category),
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'gallery_grid_partial.html', context)
    return render(request, 'index.html', context)


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

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        like_count = GalleryPostLike.objects.filter(post=post).count()
        return JsonResponse({'ok': True, 'liked': created, 'like_count': like_count})

    return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")


@login_required
def add_gallery_comment(request, post_id):
    if request.method != 'POST':
        return redirect('home')

    post = get_object_or_404(GalleryPost, id=post_id, is_visible=True)
    text = request.POST.get('comment', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not text:
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'Comment cannot be empty.'}, status=400)
        return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")

    comment = GalleryPostComment.objects.create(post=post, user=request.user, text=text[:300])
    if post.submitted_by_id != request.user.id:
        UserNotification.objects.create(
            recipient=post.submitted_by,
            actor=request.user,
            notification_type=UserNotification.NotificationType.GALLERY_COMMENT,
            gallery_post=post,
            comment=comment,
        )

    if is_ajax:
        comment_count = post.comments.count()
        return JsonResponse({
            'ok': True,
            'comment_id': comment.id,
            'username': request.user.username,
            'text': comment.text,
            'comment_count': comment_count,
        })

    return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")


@login_required
def delete_gallery_comment(request, comment_id):
    if request.method != 'POST':
        return redirect('home')

    comment = get_object_or_404(GalleryPostComment.objects.select_related('post'), id=comment_id)
    post = comment.post
    can_delete = request.user.id == comment.user_id or request.user.id == post.submitted_by_id
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not can_delete:
        if is_ajax:
            return JsonResponse({'ok': False, 'error': 'Not allowed.'}, status=403)
        messages.error(request, 'You are not allowed to delete this comment.')
        return redirect(f"{reverse_lazy('home')}#gallery-post-{post.id}")

    comment.delete()
    comment_count = post.comments.count()

    if is_ajax:
        return JsonResponse({'ok': True, 'comment_count': comment_count})

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
    )
    if request.user.is_authenticated:
        trend_reports = trend_reports.filter(
            Q(visibility=Article.Visibility.PUBLIC)
            | Q(visibility=Article.Visibility.MEMBERS)
            | Q(submitted_by=request.user)
        )
    else:
        trend_reports = trend_reports.filter(visibility=Article.Visibility.PUBLIC)

    trend_reports = trend_reports.select_related('submitted_by__profile')

    form = None
    if request.user.is_authenticated:
        form = ArticleCreateForm()

    return render(request, 'trends.html', {
        'trend_reports': trend_reports,
        'article_form': form,
    })


def full_article_page(request):
    return render(request, 'article_detail.html')


@login_required
def create_trend_article(request):
    if request.method == 'POST':
        form = ArticleCreateForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.is_trending = False
            article.moderation_status = Article.ModerationStatus.PENDING
            if not article.author_name:
                article.author_name = request.user.get_full_name() or request.user.username
            article.author = article.author_name
            article.submitted_by = request.user

            if not article.meta_description:
                article.meta_description = article.excerpt

            if article.publish_status == Article.PublishStatus.SCHEDULED and article.scheduled_publish_at:
                article.published_at = article.scheduled_publish_at.date()

            if not article.slug:
                base_slug = slugify(article.title)[:210] or 'trend-report'
                slug = base_slug
                suffix = 2
                while Article.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{suffix}"
                    suffix += 1
                article.slug = slug
            else:
                submitted_slug = slugify(article.slug)[:220]
                if not submitted_slug:
                    submitted_slug = slugify(article.title)[:210] or 'trend-report'
                slug = submitted_slug
                suffix = 2
                while Article.objects.filter(slug=slug).exclude(pk=article.pk).exists():
                    slug = f"{submitted_slug}-{suffix}"
                    suffix += 1
                article.slug = slug

            article.save()
            messages.success(request, 'Your article was submitted to admin for review. It will appear in Trend Reports after approval.')
            return redirect('trends')
    else:
        form = ArticleCreateForm()

    return render(request, 'trend_article_form.html', {'form': form})


def trend_article_detail(request, slug):
    article_qs = Article.objects.select_related('submitted_by__profile').filter(
        slug=slug,
        is_trending=True,
        moderation_status=Article.ModerationStatus.APPROVED,
    )
    if request.user.is_authenticated:
        article_qs = article_qs.filter(
            Q(visibility=Article.Visibility.PUBLIC)
            | Q(visibility=Article.Visibility.MEMBERS)
            | Q(submitted_by=request.user)
        )
    else:
        article_qs = article_qs.filter(visibility=Article.Visibility.PUBLIC)

    article = get_object_or_404(article_qs)
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
    if not article.allow_comments:
        messages.error(request, 'Comments are disabled for this article.')
        return redirect(reverse_lazy('trend-article-detail', kwargs={'slug': article.slug}))

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


@login_required
def delete_trend_article(request, slug):
    if request.method != 'POST':
        return redirect('trends')

    article = get_object_or_404(Article, slug=slug)
    can_delete = request.user.is_staff or request.user.is_superuser or request.user.id == article.submitted_by_id

    if not can_delete:
        messages.error(request, 'You are not allowed to delete this article.')
        return redirect(f"{reverse_lazy('trend-article-detail', kwargs={'slug': article.slug})}")

    article.delete()
    messages.success(request, 'Article deleted.')
    return redirect('trends')


@ensure_csrf_cookie
def insights_page(request):
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

    # Use real gallery uploads only in Latest Collection.
    outfit_cards = gallery_outfit_cards[:8]

    catalogue_items = [
        {
            'label': 'Blue',
            'image': '/static/images/blue.jpg',
            'hover_image': '/static/images/blue1.jpg',
        },
        {
            'label': 'White',
            'image': '/static/images/white.jpg',
            'hover_image': '/static/images/white1.jpg',
        },
        {
            'label': 'Black',
            'image': '/static/images/black.jpg',
            'hover_image': '/static/images/black1.jpg',
        },
        {
            'label': 'Beige',
            'image': '/static/images/beige.jpg',
            'hover_image': '/static/images/beige1.jpg',
        },
        {
            'label': 'Shirt',
            'image': '/static/images/shirt.jpg',
            'hover_image': '/static/images/shirt1.jpg',
        },
        {
            'label': 'Pants',
            'image': '/static/images/pants.jpg',
            'hover_image': '/static/images/pants1.png',
        },
        {
            'label': 'Skirt',
            'image': '/static/images/skirt.jpg',
            'hover_image': '/static/images/skirt1.jpg',
        },
        {
            'label': 'Style',
            'image': '/static/images/style.jpg',
            'hover_image': '/static/images/style1.png',
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
            _ensure_email_settings_loaded()
            if not django_settings.EMAIL_HOST_USER or not django_settings.EMAIL_HOST_PASSWORD:
                form.add_error(None, 'Email verification is not configured yet. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env.')
                return render(request, 'registration/signup.html', {'form': form})

            user = form.save(commit=False)
            user.is_active = False
            user.save()

            verification_code = f'{secrets.randbelow(1000000):06d}'
            EmailVerification.objects.update_or_create(
                user=user,
                defaults={'verification_code': verification_code},
            )

            verify_url = _build_public_url(
                request,
                reverse_lazy('verify-email'),
            )
            from django.core.mail import send_mail
            try:
                send_mail(
                    subject='Verify your FashionPulse account',
                    message=(
                        f'Hi {user.username},\n\n'
                        f'Your FashionPulse verification code is: {verification_code}\n\n'
                        f'Enter this code on the verification page:\n{verify_url}\n\n'
                        f'If you did not sign up, ignore this email.'
                    ),
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as exc:
                user.delete()
                form.add_error(None, f'Unable to send verification email: {exc}. Check Gmail SMTP settings and App Password, then try again.')
                return render(request, 'registration/signup.html', {'form': form})

            return render(request, 'registration/verification_sent.html', {'email': user.email})
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


def verify_email(request):
    email = request.POST.get('email', '').strip().lower() if request.method == 'POST' else request.GET.get('email', '').strip().lower()

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if not email or not code:
            return render(
                request,
                'registration/verification_sent.html',
                {'email': email, 'verify_error': 'Please enter both email and verification code.'},
            )

        try:
            verification = EmailVerification.objects.select_related('user').get(user__email__iexact=email)
        except EmailVerification.DoesNotExist:
            return render(request, 'registration/verification_invalid.html')

        if verification.user.is_active:
            return render(request, 'registration/verification_invalid.html')

        if verification.verification_code != code:
            return render(
                request,
                'registration/verification_sent.html',
                {'email': email, 'verify_error': 'Invalid verification code. Please try again.'},
            )

        user = verification.user
        user.is_active = True
        user.save()
        verification.delete()

        login(request, user)
        messages.success(request, 'Email verified! Welcome to FashionPulse.')
        return redirect('home')

    return render(request, 'registration/verification_sent.html', {'email': email})


@ensure_csrf_cookie
def style_lens_page(request):
    return render(request, 'style_lens.html')


@require_POST
def style_lens_analyze(request):
    """Accept an uploaded image, send it to Hugging Face for classification
    and object detection, then return detected fashion items as JSON."""
    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'ok': False, 'error': 'No image uploaded.'}, status=400)

    # Validate file type
    allowed_types = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
    if image_file.content_type not in allowed_types:
        return JsonResponse({'ok': False, 'error': 'Unsupported image format. Use JPEG, PNG, WEBP, or GIF.'}, status=400)

    # Limit file size to 10 MB
    if image_file.size > 10 * 1024 * 1024:
        return JsonResponse({'ok': False, 'error': 'Image must be under 10 MB.'}, status=400)

    token = getattr(django_settings, 'HUGGINGFACE_API_TOKEN', '')
    if not token:
        return JsonResponse({'ok': False, 'error': 'Hugging Face API token is not configured.'}, status=500)

    import json
    import urllib.request
    import urllib.error

    image_bytes = image_file.read()

    def hf_post(model_url):
        req = urllib.request.Request(
            model_url,
            data=image_bytes,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/octet-stream',
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())

    items = []
    seen_labels = set()

    # 1. Image classification (ViT) – detects clothing categories
    try:
        classifications = hf_post(
            'https://router.huggingface.co/hf-inference/models/google/vit-base-patch16-224'
        )
        for cls in classifications:
            if isinstance(cls, dict):
                label = cls.get('label', '').strip()
                score = cls.get('score', 0)
                if score >= 0.02 and label:
                    key = label.lower()
                    if key not in seen_labels:
                        seen_labels.add(key)
                        items.append({
                            'label': label.replace('_', ' ').title(),
                            'confidence': round(score * 100, 1),
                        })
    except Exception:
        pass

    # 2. Object detection (DETR) – detects accessories, bags, etc.
    try:
        detections = hf_post(
            'https://router.huggingface.co/hf-inference/models/facebook/detr-resnet-50'
        )
        for det in detections:
            if isinstance(det, dict):
                label = det.get('label', '').strip()
                score = det.get('score', 0)
                if score >= 0.5 and label and label.lower() != 'person':
                    key = label.lower()
                    if key not in seen_labels:
                        seen_labels.add(key)
                        items.append({
                            'label': label.replace('_', ' ').title(),
                            'confidence': round(score * 100, 1),
                        })
    except Exception:
        pass

    if not items:
        return JsonResponse({'ok': False, 'error': 'No fashion items detected. Try a clearer outfit photo.'}, status=200)

    items.sort(key=lambda x: x['confidence'], reverse=True)
    return JsonResponse({'ok': True, 'items': items})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    active_tab = 'tab-edit'

    if request.method == 'POST':
        if 'remove_profile_image' in request.POST:
            if profile.profile_image:
                profile.profile_image.delete(save=False)
                profile.profile_image = ''
                profile.save(update_fields=['profile_image'])
                messages.success(request, 'Profile image removed.')
            return redirect('profile')

        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was updated.')
                return redirect(f"{reverse_lazy('profile')}#tab-password")

            account_form = UserAccountForm(instance=request.user)
            profile_form = UserProfileForm(instance=profile)
            active_tab = 'tab-password'
        else:
            account_form = UserAccountForm(request.POST, instance=request.user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            password_form = PasswordChangeForm(request.user)
            if account_form.is_valid() and profile_form.is_valid():
                account_form.save()
                profile_form.save()
                messages.success(request, 'Your profile was updated.')
                return redirect('profile')
    else:
        account_form = UserAccountForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
        password_form = PasswordChangeForm(request.user)

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
    unread_notifications_count = UserNotification.objects.filter(recipient=request.user, is_read=False).count()
    profile_posts = (
        GalleryPost.objects.filter(submitted_by=request.user, is_visible=True)
        .prefetch_related('comments__user')
        .annotate(like_count=Count('likes', distinct=True), comment_count=Count('comments', distinct=True))
        .order_by('-created_at')
    )
    profile_trend_articles = (
        Article.objects.filter(submitted_by=request.user)
        .annotate(comment_count=Count('comments', distinct=True))
        .order_by('-published_at', '-created_at')
    )
    profile_liked_post_ids = set()
    if request.user.is_authenticated:
        profile_liked_post_ids = set(
            GalleryPostLike.objects.filter(user=request.user, post__in=profile_posts)
            .values_list('post_id', flat=True)
        )

    return render(
        request,
        'profile.html',
        {
            'account_form': account_form,
            'profile_form': profile_form,
            'progress_items': progress_items,
            'completion_percent': completion_percent,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'password_form': password_form,
            'active_tab': active_tab,
            'profile_posts': profile_posts,
            'profile_liked_post_ids': profile_liked_post_ids,
            'profile_trend_articles': profile_trend_articles,
        },
    )


@login_required
@require_POST
def save_profile_color(request):
    import re
    color = (request.POST.get('color') or '').strip()
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        return JsonResponse({'ok': False, 'error': 'Invalid color.'}, status=400)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.profile_color = color
    profile.save(update_fields=['profile_color'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(UserNotification, id=notification_id, recipient=request.user)
    was_unread = not notification.is_read
    if was_unread:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    unread_notifications_count = UserNotification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()
    return JsonResponse(
        {
            'ok': True,
            'marked_read': was_unread,
            'unread_count': unread_notifications_count,
        }
    )


@login_required
def list_notifications(request):
    notifications = UserNotification.objects.filter(recipient=request.user).select_related('actor', 'gallery_post', 'comment')[:50]
    items = []
    for n in notifications:
        items.append({
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%b %d, %Y %I:%M %p'),
            'gallery_post_id': n.gallery_post_id,
            'read_url': f'/notifications/{n.id}/read/',
            'delete_url': f'/notifications/{n.id}/delete/',
        })
    unread_count = sum(1 for n in notifications if not n.is_read)
    return JsonResponse({'ok': True, 'notifications': items, 'unread_count': unread_count})


@login_required
@require_POST
def delete_notification(request, notification_id):
    notification = get_object_or_404(UserNotification, id=notification_id, recipient=request.user)
    notification.delete()

    unread_notifications_count = UserNotification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()
    return JsonResponse({'ok': True, 'unread_count': unread_notifications_count})


def gallery_page(request):
    raw_gallery_category = request.GET.get('gallery_category', '').strip()
    selected_gallery_category = raw_gallery_category
    normalized_gallery_category = ''

    if raw_gallery_category:
        lowered_query = raw_gallery_category.lower()
        if lowered_query not in {'all', 'all category', 'all categories'}:
            for value, label in GalleryPost.Category.choices:
                if lowered_query in {value.lower(), label.lower()}:
                    normalized_gallery_category = value
                    break
        else:
            selected_gallery_category = ''

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

    context = {
        'gallery_posts': gallery_posts,
        'liked_post_ids': liked_post_ids,
        'selected_gallery_category': selected_gallery_category,
        'gallery_category_choices': GalleryPost.Category.choices,
        'gallery_filter_active': bool(normalized_gallery_category),
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'gallery_grid_partial.html', context)
    return render(request, 'gallery.html', context)


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

    trend_articles = Article.objects.filter(submitted_by=owner).annotate(comment_count=Count('comments', distinct=True))
    total_photo_likes = sum(post.like_count for post in posts)
    total_article_comments = sum(article.comment_count for article in trend_articles)

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
            'total_photo_likes': total_photo_likes,
            'total_article_comments': total_article_comments,
        },
    )
