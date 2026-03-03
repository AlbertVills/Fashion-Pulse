from django.urls import path

from .views import (
    about_page,
    article_list,
    contact_page,
    full_article_page,
    insights_page,
    profile_view,
    signup_view,
    trends_page,
)

urlpatterns = [
    path('', article_list, name='home'),
    path('trends/', trends_page, name='trends'),
    path('article/minimalist-power-dressing/', full_article_page, name='article-detail'),
    path('insights/', insights_page, name='insights'),
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),
]
