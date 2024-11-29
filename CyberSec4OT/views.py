from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django import forms
import requests
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from functools import wraps
from datetime import datetime, timedelta

def faq(request):
    # Render the dashboard template and pass the request.user object
    return render(request, 'faq.html', {
        'user': request.user,
    })

def home_view(request):
    # Logic for rendering the homepage goes here
    return render(request, 'home.html')  # Replace 'home.html' with your actual home template

# Request demo view
def request_demo_view(request):
    # Logic for requesting demo goes here
    return render(request, 'request_demo.html')  # Replace 'request_demo.html' with your request demo template


# Enroll for individual plan view
def enroll_individual_view(request):
    # Logic for enrolling for individual plan goes here
    return render(request,
                  'enroll_individual.html')  # Replace 'enroll_individual.html' with your enroll individual template


# Enroll for a school view
def enroll_school_view(request):
    # Logic for enrolling for a school goes here
    return render(request, 'enroll_school.html')  # Replace 'enroll_school.html' with your enroll school template

class FAQForAllView(TemplateView):
    template_name = 'faq_for_all.html'

def about_view(request):
    # Logic for rendering the about page goes here
    return render(request, 'about.html')

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)

def verify_recaptcha(recaptcha_response):
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': settings.RECAPTCHA_KEYS['login']['secret_key'],
        'response': recaptcha_response
    }
    response = requests.post(verify_url, data=data)
    return response.json()['success']

def rate_limit_contact_us(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Use IP address or user ID as the key
        user_key = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anonymous')
        cache_key = f'contact_us_rate_{user_key}'

        # Get request timestamps from cache
        attempts = cache.get(cache_key, [])
        current_time = datetime.now()

        # Filter timestamps older than 30 minutes
        valid_attempts = [timestamp for timestamp in attempts if current_time - timestamp < timedelta(minutes=30)]

        if len(valid_attempts) > 4:  # Maximum 4 messages per 30 minutes
            messages.error(
                request,
                "You have reached the maximum number of submissions (4) in 30 minutes. Please try again later.",
                extra_tags='error',
            )
            return render(request, 'contact_us.html', {
                'form': ContactForm(),
                'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_KEYS['contact_us']['site_key']
            })

        # Record the current attempt
        valid_attempts.append(current_time)
        cache.set(cache_key, valid_attempts, timeout=1800)  # Cache for 30 minutes

        return view_func(request, *args, **kwargs)
    return wrapper


@rate_limit_contact_us
def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        captcha_response = request.POST.get('g-recaptcha-response')

        # Verify CAPTCHA
        data = {
            'secret': settings.RECAPTCHA_KEYS['contact_us']['secret_key'],
            'response': captcha_response,
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()

        if not result.get('success'):
            messages.error(request, 'Please complete the CAPTCHA.')
            return render(request, 'contact_us.html', {
                'form': form,
                'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_KEYS['contact_us']['site_key']
            })

        if form.is_valid():
            try:
                # Construct the email message
                email_message = f"""
                New contact form submission:
                
                Name: {form.cleaned_data['name']}
                Email: {form.cleaned_data['email']}
                Subject: {form.cleaned_data['subject']}
                Message: {form.cleaned_data['message']}
                """

                # Send email
                send_mail(
                    subject=f'Contact Form: {form.cleaned_data["subject"]}',
                    message=email_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=['cyberotsec@gmail.com'],
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('contact_us')
            except Exception as email_error:
                error_message = f"An error occurred while sending your message: {str(email_error)}"
                messages.error(request, error_message)
                return render(request, 'contact_us.html', {
                    'form': form,
                    'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_KEYS['contact_us']['site_key']
                })
    else:
        form = ContactForm()

    return render(request, 'contact_us.html', {
        'form': form,
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_KEYS['contact_us']['site_key']
    })