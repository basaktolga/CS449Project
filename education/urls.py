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
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "education"

urlpatterns = [
    path('courses/filter/', views.filter_available_courses, name='filter_available_courses'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('courses/', views.all_courses, name='all_courses'),
    path('courses/available/', views.available_courses, name='available_courses'),
    path('courses/owned/', views.owned_courses, name='owned_courses'),
    path('courses/filter_owned/', views.filter_owned_courses, name='filter_owned_courses'),
    path('courses/filter_available/', views.filter_available_courses, name='filter_available_courses'),
    path('paths/', views.paths, name='paths'),
    path('courses/<slug:slug>/', views.course_page, name='course_page'),
    path('courses/<slug:slug>/enroll/', views.enroll_in_course, name='enroll_in_course'),
    path('courses/<slug:slug>/enrolled/', views.enrolled_course, name='enrolled_course'),
    path('lecturers/<int:lecturer_id>/', views.lecturer_profile, name='lecturer_profile'),
    path('filter/', views.filter_courses, name='filter_courses'),
    path('my-badges/', views.my_badges, name='my_badges'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('certificate-validation/', views.certificate_validation, name='certificate_validation'),
    #path('certificate/<uuid:cert_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificate_detail/<uuid:user_certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('course/<slug:slug>/', views.course_page, name='course_detail'),
    path('paths/filter/', views.filter_paths, name='filter_paths'),
    path('paths/<slug:path_id>/', views.path_detail, name='path_detail'),

]


if settings.DEBUG:  # Serve uploaded files during development
    urlpatterns += static('/certificates/', document_root='certificates/')