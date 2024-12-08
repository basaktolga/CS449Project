"""
URL configuration for CyberSec4OT project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from . import views
from .views import FAQForAllView
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

def custom_404(request, exception):
    return render(request, '404.html', status=404)

# Non-localized URLs (URLs that shouldn't have language prefix)
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
]

# Localized URLs - these will have language prefix
urlpatterns += i18n_patterns(
    path('', views.home_view, name='home'),
    path('request-demo/', views.request_demo_view, name='request_demo'),
    path('faq_for_all/', FAQForAllView.as_view(), name='faq_for_all'),
    path('faq/', views.faq, name='faq'),
    path('about/', views.about_view, name='about'),
    path('', include('education.urls')),
    path('surveys/', include('surveys.urls')),
    path('', include("accounts.urls")),
    path('', include("payment.urls")),
    path('contact_us/', views.contact_us, name='contact_us'),
    prefix_default_language=True  # This will add prefix for default language too
)

if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'CyberSec4OT.urls.custom_404'