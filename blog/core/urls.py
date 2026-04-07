"""
URL configuration for blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.urls import reverse_lazy

from articles.views import (
    AdminAwareLoginView,
    logout_view,
    password_reset_code_confirm,
    password_reset_request_code,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', AdminAwareLoginView.as_view(), name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path(
        'accounts/password_reset/',
        password_reset_request_code,
        name='password_reset',
    ),
    path('accounts/password-reset-code/', password_reset_code_confirm, name='password_reset_code_confirm'),
    path(
        'accounts/password-change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
            success_url=reverse_lazy('profile'),
        ),
        name='user_password_change',
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('articles.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
