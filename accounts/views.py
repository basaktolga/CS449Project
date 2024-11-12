from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, TicketForm, TicketResponseForm
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .models import  Notification, Reminder
from django.conf import settings
import requests
from django.utils import timezone
from .models import Ticket
from django.http import JsonResponse
import json
from .models import UserActivityLog

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("education:user_dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'settings.html'
    success_url = reverse_lazy('accounts:settings')  # Redirect to the 'settings' page after success

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.", extra_tags='success settings-related')
        return super().form_valid(form)

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('delete_password')
        confirm_password = request.POST.get('confirm_delete_password')

        if password and password == confirm_password:
            user = request.user
            if user.check_password(password):
                user.delete()
                messages.success(request, "Your account has been deleted successfully.", extra_tags='success settings-related')
                return redirect('accounts:login')  # Redirect to the home page or another page after deletion
            else:
                messages.error(request, "Incorrect password.", extra_tags='error settings-related')
        else:
            messages.error(request, "Passwords do not match.", extra_tags='error settings-related')
    
    return render(request, 'settings.html')


@login_required
def send_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)

        captcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,  
            'response': captcha_response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()

        if not result.get('success'):
            messages.error(request, 'Please complete the CAPTCHA.')
            return render(request, 'send_ticket.html', {'form': form})


        
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user  # Associate the ticket with the current user
            ticket.status = 'Open'  # Set the default status to 'Open'
            ticket.save()
            messages.success(request, 'Your ticket has been submitted successfully.')
            Notification.objects.create(
                user=request.user,
                message=f"Your ticket: {ticket.title} submitted.",
                is_read=False
            )
            return redirect('accounts:send_ticket')  # Replace with your actual success URL
        else:
            print(form.errors)
            messages.error(request, 'There was an error submitting your ticket. Please try again.')

    else:
        form = TicketForm()

    #return render(request, 'send_ticket.html', {'form': form})
    return render(request, 'send_ticket.html', {'form': form, 'RECAPTCHA_SITE_KEY': settings})


@login_required
def my_tickets(request):
    if request.user.is_staff:  # Check if the user is an admin
        tickets = Ticket.objects.all()  # Admin sees all tickets
    else:
        tickets = Ticket.objects.filter(user=request.user)  # Regular user sees only their tickets

    context = {
        'tickets': tickets,

    }

    return render(request, 'my_tickets.html', context)

@login_required
def close_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)  # Ensure the ticket belongs to the user
    if ticket.status == 'Open':  # Check if the ticket is open
        ticket.status = 'Closed'
        ticket.save()
        messages.success(request, 'Your ticket has been closed.')
        Notification.objects.create(
            user=request.user,
            message=f"Your ticket: {ticket.title} has been closed.",
            is_read=False
        )

    else:
        messages.error(request, 'Ticket cannot be closed because it is already closed or does not belong to you.')
    return redirect('my_tickets')  # Redirect to the my_tickets page after closing the ticket


def insert_newlines(text, limit=100):
    """Inserts newlines into the text after a specified character limit."""
    if not text:
        return text
    return '\n'.join([text[i:i + limit] for i in range(0, len(text), limit)])


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Format the topic directly
    ticket.topic = insert_newlines(ticket.topic, limit=80)

    # Format the responses list directly with newlines
    responses_list = insert_newlines(ticket.responses, limit=100).splitlines() if ticket.responses else []

    if request.method == 'POST':
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response_message = form.cleaned_data['message']
            # Add a blank line before the user's response
            response = f"\n{request.user.username}: {response_message} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Initialize responses if None or empty, else append
            if ticket.responses is None or ticket.responses.strip() == '':
                ticket.responses = response
            else:
                ticket.responses += response

            ticket.save()
            # Update the responses list again after saving
            responses_list = insert_newlines(ticket.responses, limit=120).splitlines()
            return redirect('accounts:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()

    return render(request, 'ticket_detail.html', {
        'ticket': ticket,
        'form': form,
        'responses_list': responses_list,
    })

def activity_log_view(request):
    if request.user.is_authenticated:
        last_activity = UserActivityLog.objects.filter(user=request.user).order_by('-timestamp').first()
        activity_logs = UserActivityLog.objects.filter(user=request.user).order_by('-timestamp')
    else:
        last_activity = None
        activity_logs = []

    return render(request, 'activity_log.html', {
        'last_activity': last_activity,
        'activity_logs': activity_logs
    })

def save_location(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is not None and longitude is not None:
            # Save the location or use a service to get the city/country from the coordinates
            location = f"{latitude}, {longitude}"

            # You can update the user's activity log here
            UserActivityLog.objects.create(
                user=request.user,
                activity="Logged in with location",
                location=location
            )
            
            return JsonResponse({'status': 'success', 'location': location})
        else:
            return JsonResponse({'status': 'error', 'message': 'Unable to get location'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def get_city_from_coords(latitude, longitude):
    # Use a reverse geocoding API (like Google Maps or OpenCage)
    response = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key=YOUR_API_KEY")
    data = response.json()
    if data['results']:
        return data['results'][0]['formatted']
    return "Unknown location"
        
        
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})


def get_reminders(request):
    reminders = Reminder.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'reminders.html', {'reminders': reminders})


def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')


def base_view(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    reminders = Reminder.objects.filter(user=request.user)
    return {'notifications': notifications, 'reminders': reminders}