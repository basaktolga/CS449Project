from django.shortcuts import render
from django.views.generic import TemplateView

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

from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

@require_POST
def contact(request):
    email = request.POST.get('email')
    subject = request.POST.get('subject')
    message = request.POST.get('message')
    
    try:
        send_mail(
            subject=f"Contact Form: {subject}",
            message=f"From: {email}\n\n{message}",
            from_email=email,
            recipient_list=['admin@cybersec4ot.com'],
            fail_silently=False,
        )
        messages.success(request, 'Your message has been sent successfully!')
    except Exception as e:
        messages.error(request, 'There was an error sending your message. Please try again later.')
    
    return redirect(request.META.get('HTTP_REFERER', '/')) 