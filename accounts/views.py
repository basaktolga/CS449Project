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
from .utils import get_client_ip, get_geolocation, get_ip_reputation
from django.http import HttpResponse
import csv


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            from .models import UserActivityLog
            ip_address = get_client_ip(request)
            location = get_geolocation(ip_address)
            UserActivityLog.objects.create(
                user=user,
                attempt_type='New User Signed Up',
                url_visited=request.path,
                ip_address=request.META.get('REMOTE_ADDR'),
                http_status='201 Created',
                location=location
            )
            
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
        ip_address = get_client_ip(request)
        location = get_geolocation(ip_address)
        captcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,  
            'response': captcha_response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()

        if not result.get('success'):
            messages.error(request, 'Please complete the CAPTCHA.')
             # Log failure due to CAPTCHA
            UserActivityLog.objects.create(
                user=request.user,
                attempt_type='Failed to Submit Ticket',
                url_visited='/send_ticket/',
                ip_address = ip_address,
                http_status='403 Forbidden',
                location = location
                
            )
            return render(request, 'send_ticket.html', {'form': form})


        
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user  # Associate the ticket with the current user
            ticket.status = 'Open'  # Set the default status to 'Open'
            ticket.save()
            UserActivityLog.objects.create(
                user=request.user,
                attempt_type='Submitted Ticket',
                url_visited='/send_ticket/',
                ip_address = ip_address,
                http_status='200 OK',
                location = location
                
            )
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
            UserActivityLog.objects.create(
                user=request.user,
                attempt_type='Failed to Submit Ticket',
                url_visited='/send_ticket/',
                ip_address = ip_address,
                http_status='400 Bad Request',
                location=location
            )

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
    ip_address = get_client_ip(request)
    location = get_geolocation(ip_address)
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
        UserActivityLog.objects.create(
            user=request.user,
            attempt_type='Ticket is Closed',
            url_visited=f"/ticket/{ticket.id}/",
            ip_address = ip_address,
            http_status='200 OK',
            location=location
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
    from .models import UserActivityLog
    filter_type = request.GET.get("filter", "all")  # Get the selected filter type
    export_csv = request.GET.get('export') == 'csv'

    # Define log filtering based on the selected filter type
    if filter_type == "auth":
        logs = UserActivityLog.objects.filter(
            user=request.user,
            attempt_type__in=["Logged In", "Logged Out", "Failed to Log In"]
        )
        csv_filename = "auth_based_logs.csv"
    elif filter_type == "activity":
        logs = UserActivityLog.objects.filter(user=request.user).exclude(
            attempt_type__in=["Logged In", "Logged Out", "Failed to Log In", "Page Visit"]
        )
        csv_filename = "activity_based_logs.csv"
    else:
        logs = UserActivityLog.objects.filter(user=request.user).exclude(
            attempt_type="Page Visit"
        )
        csv_filename = "all_logs.csv"

    # Export CSV if requested
    if export_csv:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{csv_filename}"'

        writer = csv.writer(response)
        writer.writerow(['User', 'Attempt Type', 'IP Address', 'HTTP Status', 'Location', 'Timestamp'])

        for log in logs:
            if log.timestamp:
                localized_timestamp = timezone.localtime(log.timestamp)
                formatted_timestamp = localized_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_timestamp = 'N/A'
            
            writer.writerow([
                request.user.username if log.user else 'Unknown',
                log.attempt_type,
                log.ip_address,
                log.http_status,
                log.location,
                formatted_timestamp,
            ])

        # Export visited URLs section for all filters
        writer.writerow([])  # Blank row for separation
        writer.writerow(['Visited URLs'])  # Header for URLs section
        writer.writerow(['URL', 'Timestamp'])

        visited_urls = UserActivityLog.objects.filter(
            user=request.user,
            attempt_type="Page Visit"
        ).values('url_visited', 'timestamp')

        for url in visited_urls:
            writer.writerow([url['url_visited'], url['timestamp']])

        return response  # Return CSV response immediately

    # List of local IP addresses to hide
    local_ip_blacklist = ['127.0.0.1', '192.168.1.1', '10.0.0.1'] 

    def hide_local_ip(log_entry):
        """Hide IP and location if the IP address is in the blacklist."""
        if log_entry.ip_address in local_ip_blacklist:
            log_entry.ip_address = ' '
            log_entry.location = ' '
        return log_entry

    if request.user.is_authenticated:
        url_visited = UserActivityLog.objects.filter(user=request.user, attempt_type="Page Visit").values('url_visited', 'timestamp')
        
        if filter_type == "auth":
            last_attempts = UserActivityLog.objects.filter(
                user=request.user,
                attempt_type__in=["Logged In", "Logged Out", "Failed to Log In"]
            ).order_by('-timestamp')
        elif filter_type == "activity":
            last_attempts = UserActivityLog.objects.filter(
                user=request.user
            ).exclude(attempt_type__in=["Logged In", "Logged Out", "Failed to Log In", "Page Visit"]).order_by('-timestamp')
        else:
            last_attempts = UserActivityLog.objects.filter(
                user=request.user
            ).exclude(attempt_type="Page Visit").order_by('-timestamp')

        # Check each log's IP address and clear it if in blacklist
        last_attempts = [hide_local_ip(log) for log in last_attempts]

        last_successful_login = UserActivityLog.objects.filter(
            user=request.user,
            attempt_type='Logged In'
        ).order_by('-timestamp').first()

        last_unsuccessful_login = UserActivityLog.objects.filter(
            user=request.user,
            attempt_type='Failed to Log In'
        ).order_by('-timestamp').first()

        if last_successful_login:
            last_successful_login = hide_local_ip(last_successful_login)
        if last_unsuccessful_login:
            last_unsuccessful_login = hide_local_ip(last_unsuccessful_login)
    else:
        last_successful_login = None
        last_unsuccessful_login = None
        last_attempts = []
        url_visited = []

    return render(request, 'activity_log.html', {
        'last_successful_login': last_successful_login,
        'last_unsuccessful_login': last_unsuccessful_login,
        'last_attempts': last_attempts,
        'filter_type': filter_type,
        'url_visited': url_visited
    })

def check_ip_in_user_view(request):
    user_ip = request.META.get('REMOTE_ADDR')
    ip_data = get_ip_reputation(user_ip)
    # Process and store the IP reputation data as needed



        
        
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