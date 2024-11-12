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