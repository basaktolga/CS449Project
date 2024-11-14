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
from . import views
from .views import FAQForAllView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('request-demo/', views.request_demo_view, name='request_demo'),
    path('faq_for_all/', FAQForAllView.as_view(), name='faq_for_all'),
    path('about/', views.about_view, name='about'),  # URL pattern for the about page
    path('contact/', views.contact, name='contact'),
    # URL pattern for the request demo page
    path('enroll-individual/', views.enroll_individual_view, name='enroll_individual'),
    # URL pattern for enrolling for individual plan
    path('enroll-school/', views.enroll_school_view, name='enroll_school'),
    path('', include('education.urls')),
    path('surveys/', include('surveys.urls')),
    path('', include("accounts.urls")),
    path('', include("payment.urls")),
    path('faq/', views.faq, name='faq'),  # URL pattern for faq
]
