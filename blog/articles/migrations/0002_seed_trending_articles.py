from django.db import migrations


def seed_articles(apps, schema_editor):
    Article = apps.get_model('articles', 'Article')

    entries = [
        {
            'title': 'Streetwear Tailoring Takes Over 2026',
            'slug': 'streetwear-tailoring-takes-over-2026',
            'excerpt': 'Relaxed suiting meets sneaker culture in the biggest crossover trend this season.',
            'content': 'Fashion weeks are highlighting oversized blazers, wide-leg trousers, and technical sneakers styled together for daily wear.',
            'author': 'Fashion Desk',
            'is_trending': True,
            'published_at': '2026-03-01',
        },
        {
            'title': 'Quiet Luxury Colors Shift to Soft Earth Tones',
            'slug': 'quiet-luxury-colors-soft-earth-tones',
            'excerpt': 'Neutral wardrobes now lean warmer, with clay, olive, and sand dominating collections.',
            'content': 'Designers are balancing minimal silhouettes with rich natural palettes, making essentials feel elevated without heavy branding.',
            'author': 'Style Weekly',
            'is_trending': True,
            'published_at': '2026-02-28',
        },
        {
            'title': 'Denim-on-Denim Returns with Modern Cuts',
            'slug': 'denim-on-denim-modern-cuts',
            'excerpt': 'The classic double-denim look is back, updated with structured shapes and cleaner washes.',
            'content': 'From cropped jackets to barrel jeans, coordinated denim outfits are being styled for both casual and semi-formal occasions.',
            'author': 'Runway Monitor',
            'is_trending': True,
            'published_at': '2026-02-27',
        },
        {
            'title': 'Athleisure 2.0 Blends Performance and Officewear',
            'slug': 'athleisure-2-0-performance-officewear',
            'excerpt': 'Technical fabrics are moving into smart-casual outfits designed for hybrid work routines.',
            'content': 'Breathable knits, stretch trousers, and polished zip layers are defining a practical style direction for city professionals.',
            'author': 'Trend Lab',
            'is_trending': True,
            'published_at': '2026-02-25',
        },
        {
            'title': 'Vintage Accessories Lead Social Media Styling',
            'slug': 'vintage-accessories-social-media-styling',
            'excerpt': 'Retro belts, shoulder bags, and statement eyewear are driving high-engagement outfit posts.',
            'content': 'Creators are mixing thrifted accessories with contemporary basics to build personalized looks that feel both nostalgic and fresh.',
            'author': 'Fashion Desk',
            'is_trending': True,
            'published_at': '2026-02-24',
        },
    ]

    for entry in entries:
        Article.objects.get_or_create(slug=entry['slug'], defaults=entry)


def unseed_articles(apps, schema_editor):
    Article = apps.get_model('articles', 'Article')
    slugs = [
        'streetwear-tailoring-takes-over-2026',
        'quiet-luxury-colors-soft-earth-tones',
        'denim-on-denim-modern-cuts',
        'athleisure-2-0-performance-officewear',
        'vintage-accessories-social-media-styling',
    ]
    Article.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_articles, unseed_articles),
    ]
