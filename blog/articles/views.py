from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render

from .forms import ContactForm, SignUpForm, UserAccountForm, UserProfileForm
from .models import Article, ContactMessage, UserProfile


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

    gallery_items = [
        {'image': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80', 'title': 'Monochrome Street Layering'},
        {'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80', 'title': 'Relaxed Suiting in Motion'},
        {'image': 'https://images.unsplash.com/photo-1502716119720-b23a93e5fe1b?auto=format&fit=crop&w=900&q=80', 'title': 'Soft Utility Styling'},
        {'image': 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80', 'title': 'Off-Duty Editorial Looks'},
        {'image': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=80', 'title': 'Textured Neutral Pairings'},
        {'image': 'https://images.unsplash.com/photo-1551163943-3f6a855d1153?auto=format&fit=crop&w=900&q=80', 'title': 'Urban Tailoring and Sneakers'},
    ]

    return render(
        request,
        'index.html',
        {
            'trending_stories': trending_stories,
            'gallery_items': gallery_items,
        },
    )


def trends_page(request):
    trend_reports = [
        {'title': 'Spring / Summer 2026 Trend Forecast', 'season': 'Spring/Summer 2026', 'theme': 'Minimalism', 'style': 'Tailored', 'date': '2026-03-01', 'excerpt': 'Seasonal direction focused on clean proportions and practical elegance.', 'image': '/static/images/spring summer.png'},
        {'title': 'Autumn Layers and Texture Forecast', 'season': 'Autumn/Winter 2026', 'theme': 'Texture', 'style': 'Layered', 'date': '2026-02-20', 'excerpt': 'Material contrast drives storytelling through knitwear and outerwear.', 'image': '/static/images/autumn.jpg'},
        {'title': 'Resort 2026 Urban Ease Report', 'season': 'Resort 2026', 'theme': 'Mobility', 'style': 'Streetwear', 'date': '2026-02-12', 'excerpt': 'Designers prioritize movement with lightweight utility silhouettes.', 'image': '/static/images/resort.jpg'},
        {'title': 'Power Basics in Retail Edit', 'season': 'Spring/Summer 2026', 'theme': 'Commercial', 'style': 'Minimal', 'date': '2026-02-05', 'excerpt': 'High-conviction essentials dominate both luxury and premium markets.', 'image': '/static/images/retail.jpg'},
        {'title': 'Color Rhythm: 2026 Mid-Year Outlook', 'season': 'Mid-Year 2026', 'theme': 'Color', 'style': 'Contemporary', 'date': '2026-01-30', 'excerpt': 'Warm muted tones continue to outperform saturated brights globally.', 'image': '/static/images/color rhythm.png'},
        {'title': 'Street Heritage and Luxury Blends', 'season': 'Autumn/Winter 2026', 'theme': 'Heritage', 'style': 'Hybrid', 'date': '2026-01-22', 'excerpt': 'Legacy tailoring codes merge with street-led styling language.', 'image': '/static/images/street heritage.jpg'},
    ]
    trend_reports = sorted(trend_reports, key=lambda item: item['date'], reverse=True)
    return render(request, 'trends.html', {'trend_reports': trend_reports})


def full_article_page(request):
    return render(request, 'article_detail.html')


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

    return render(
        request,
        'profile.html',
        {
            'account_form': account_form,
            'profile_form': profile_form,
            'progress_items': progress_items,
            'completion_percent': completion_percent,
        },
    )
