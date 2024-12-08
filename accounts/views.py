from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
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
from django.utils import timezone
from datetime import timedelta
from .models import VerificationCode
import random
import string
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from .decorators import rate_limit_verification_codes
from django.utils.decorators import method_decorator
from django.core.cache import cache
from datetime import datetime
from .mixins import RateLimitMixin


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

class CustomPasswordChangeView(RateLimitMixin, PasswordChangeView):
    template_name = 'settings.html'
    success_url = reverse_lazy('accounts:verify_action')

    def form_valid(self, form):
        if not self.check_rate_limit():
            return redirect('accounts:settings')

        try:
            # Create verification code using the class method
            verification = VerificationCode.create_verification(
                user=self.request.user,
                action='change_password',
                data={'new_password_hash': make_password(form.cleaned_data['new_password1'])}
            )

            # Send the code to user's email
            send_mail(
                'Your Verification Code',
                f'Your verification code is {verification.code}',
                'cyberotsec@gmail.com',
                [self.request.user.email],
                fail_silently=False,
            )

            messages.info(self.request, "A verification code has been sent to your email.")
            return redirect('accounts:verify_action')
        except Exception as e:
            messages.error(self.request, f"Error creating verification code: {str(e)}")
            return redirect('accounts:settings')

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error, extra_tags='error settings-related')
        return super().form_invalid(form)

@login_required
@rate_limit_verification_codes
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('delete_password')
        confirm_delete = request.POST.get('confirm_delete')

        if confirm_delete == 'DELETE MY ACCOUNT':
            user = request.user
            if user.check_password(password):
                try:
                    # Create verification code using the class method
                    verification = VerificationCode.create_verification(
                        user=user,
                        action='delete_account'
                    )

                    # Send the code to user's email
                    send_mail(
                        'Your Verification Code',
                        f'Your verification code is {verification.code}',
                        'cyberotsec@gmail.com',
                        [user.email],
                        fail_silently=False,
                    )

                    messages.info(request, "A verification code has been sent to your email.")
                    return redirect('accounts:verify_action')
                except Exception as e:
                    messages.error(request, f"Error creating verification code: {str(e)}", 
                                 extra_tags='error settings-related')
                    return redirect('accounts:settings')
            else:
                messages.error(request, "Incorrect password.", extra_tags='error settings-related')
        else:
            messages.error(request, "Please type 'DELETE MY ACCOUNT' to confirm.", 
                         extra_tags='error settings-related')
    return render(request, 'settings.html')

@login_required
def verify_action(request):
    if request.method == 'POST':
        code_input = request.POST.get('code')
        user = request.user

        try:
            # First check if there's any valid verification code for this user
            verification = VerificationCode.objects.filter(
                user=user,
                code=code_input
            ).first()

            if not verification:
                messages.error(request, "Invalid verification code.", extra_tags='error settings-related')
                return render(request, 'verify_action.html')

            if verification.is_valid():
                action = verification.action

                if action == 'change_password':
                    try:
                        # Get the new password hash from verification.data
                        new_password_hash = verification.data.get('new_password_hash')
                        if not new_password_hash:
                            messages.error(request, "Password data not found.", extra_tags='error settings-related')
                            return render(request, 'verify_action.html')

                        # Update password
                        user.password = new_password_hash
                        user.save()

                        # Delete verification code after successful password change
                        verification.delete()

                        messages.success(request, "Your password has been changed successfully.")
                        update_session_auth_hash(request, user)
                        return redirect('accounts:settings')

                    except Exception as e:
                        messages.error(request, f"Error changing password: {str(e)}", extra_tags='error settings-related')
                        return render(request, 'verify_action.html')

                elif action == 'delete_account':
                    try:
                        # Delete verification code first
                        verification.delete()
                        
                        # Then delete user
                        user.delete()
                        messages.success(request, "Your account has been deleted successfully.", extra_tags='success settings-related')
                        return redirect('accounts:login')

                    except Exception as e:
                        messages.error(request, f"Error deleting account: {str(e)}", extra_tags='error settings-related')
                        return render(request, 'verify_action.html')

                else:
                    messages.error(request, "Invalid action.", extra_tags='error settings-related')
            else:
                messages.error(request, "Verification code has expired.", extra_tags='error settings-related')
                verification.delete()
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}", extra_tags='error settings-related')

    return render(request, 'verify_action.html')

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
    return redirect('accounts:my_tickets')  # Redirect to the my_tickets page after closing the ticket 

"""
def insert_newlines(text, limit=100):
    #Inserts newlines into the text after a specified character limit.
    if not text:
        return text
    return '\n'.join([text[i:i + limit] for i in range(0, len(text), limit)])
"""
"""
@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Format the topic directly
    #ticket.topic = insert_newlines(ticket.topic, limit=80)

    # Format the responses list directly with newlines
    #responses_list = insert_newlines(ticket.responses, limit=100).splitlines() if ticket.responses else []
    responses_list = ticket.responses.splitlines() if ticket.responses else []

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
            #responses_list = insert_newlines(ticket.responses, limit=300).splitlines()
            responses_list = ticket.responses.splitlines()
            return redirect('accounts:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()

    return render(request, 'ticket_detail.html', {
        'ticket': ticket,
        'form': form,
        'responses_list': responses_list,
    })


"""
"""

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

   
    responses_list = ticket.responses.splitlines() if ticket.responses else []

    if request.method == 'POST':
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response_message = form.cleaned_data['message']
            # Add a formatted response
            response = f"{request.user.username}: {response_message} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Append response
            if not ticket.responses:
                ticket.responses = response
            else:
                ticket.responses += response

            ticket.save()
            responses_list = ticket.responses.splitlines()
            return redirect('accounts:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()

    return render(request, 'ticket_detail.html', {
        'ticket': ticket,
        'form': form,
        'responses_list': responses_list,
    })

"""

from django.utils.timezone import localtime
from django.utils.html import escape

def insert_newline(text):
    text = escape(text)
    return text.replace("\n", "<br>")

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    import logging
    logger = logging.getLogger(__name__)

    logger.debug(f"Raw responses: {ticket.responses}")


    admin_responses = []
    user_responses = []

    # Process the entire responses text as a sequence of messages
    if ticket.responses:
        # Assume messages are separated by a special delimiter like '\n\n' or just '\n'
        messages = ticket.responses.split("\n\n")  # Use double newline to differentiate messages
        """
        for message in messages:
            if ":" not in message or "-" not in message:
                continue  # Skip malformed entries

            try:
                username, remainder = message.split(":", 1)
                text, timestamp = remainder.rsplit(".", 1)
            except ValueError:
                continue  # Skip malformed entries

            username = username.strip()
            text = text.strip()
            timestamp = timestamp.strip()

            user_obj = User.objects.filter(username=username).first()
            if user_obj and user_obj.is_superuser:
                admin_responses.append({
                    'username': username,
                    'message': insert_newline(text),
                    'timestamp': timestamp
                })
            elif user_obj:
                user_responses.append({
                    'username': username,
                    'message': insert_newline(text),
                    'timestamp': timestamp
                })
        """
        
        for message in messages:
            logger.debug(f"Processing message: {message}")
            if ":" in message and "." in message:
                # Assume the format is: username: message - timestamp
                try:
                    username, remainder = message.split(":", 1)
                    text, timestamp = remainder.rsplit(".", 1)
                    username = username.strip()
                    text = text.strip()
                    timestamp = timestamp.strip()
                    

                    # Simplify admin/user distinction
                    is_admin = User.objects.filter(username=username, is_superuser=True).exists()
                    response_data = {
                        'username': username,
                        'message': insert_newline(text),
                        'timestamp': timestamp
                    }
                    if is_admin:
                        admin_responses.append(response_data)
                    else:
                        user_responses.append(response_data)
                    """
                    # Check if user exists
                    user_obj = User.objects.filter(username=username).first()
                    if user_obj and user_obj.is_superuser:  # Admin response
                    
                        admin_responses.append({
                            'username': username,
                            'message': insert_newline(text),
                            'timestamp': timestamp
                        })
                    elif user_obj:  # User response
                        user_responses.append({
                            'username': username,
                            'message': insert_newline(text),
                            'timestamp': timestamp
                        })
                    """
                    logger.debug(f"Parsed: {username}, {text}, {timestamp}, Is Admin: {is_admin}")
                except ValueError:
                
                    logger.error(f"Malformed response skipped: {message}")
                    # Ignore malformed entries
                    continue
                    
    # Handle the form submission for adding new responses
    if request.method == 'POST':
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response_message = form.cleaned_data['message']
            response = f"{request.user.username}: {response_message} . {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            #response = f"{request.user.username}:  {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n" - {response_message}

            if not ticket.responses:
                ticket.responses = response
            else:
                ticket.responses += response

            ticket.save()
            return redirect('accounts:ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketResponseForm()

    return render(request, 'ticket_detail.html', {
        'ticket': ticket,
        'form': form,
        'admin_responses': admin_responses,
        'user_responses': user_responses,
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

        #if last_successful_login:
        #    last_successful_login = hide_local_ip(last_successful_login)
        #if last_unsuccessful_login:
        #    last_unsuccessful_login = hide_local_ip(last_unsuccessful_login)
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

def login_view(request):
    if request.method == 'POST':
        # Verify eye-tracking CAPTCHA
        captcha_solved = request.POST.get('captcha-solved') == 'true'
        
        if not captcha_solved:
            messages.error(request, 'Please complete the eye-tracking CAPTCHA.')
            return render(request, 'login.html')
        
        # Continue with your existing login logic
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('education:user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        # Verify reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': '6LdpXVsqAAAAAOQsUZcpCcEY5CGO90lOdF_GJH-P',
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        
        if not result['success']:
            messages.error(request, 'Please complete the reCAPTCHA.')
            return redirect('register')
            
        # Continue with your existing registration logic

@login_required
@rate_limit_verification_codes
def resend_verification_code(request):
    if request.method == 'POST':
        user = request.user
        try:
            # Get the existing verification code
            verification = VerificationCode.objects.filter(user=user).latest('created_at')
            
            if not verification:
                messages.error(request, "No verification process in progress.", extra_tags='error')
                return redirect('accounts:settings')

            # Create new verification code
            new_verification = VerificationCode.create_verification(
                user=user,
                action=verification.action,
                data=verification.data
            )

            # Delete old verification code
            verification.delete()

            # Send the new code
            send_mail(
                'Your New Verification Code',
                f'Your new verification code is {new_verification.code}',
                'cyberotsec@gmail.com',
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "A new verification code has been sent to your email.")
            
        except Exception as e:
            messages.error(request, f"Error sending new verification code: {str(e)}", extra_tags='error')
            
    return redirect('accounts:verify_action')

def logout_view(request):
    logout(request)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect(settings.LOGOUT_REDIRECT_URL)