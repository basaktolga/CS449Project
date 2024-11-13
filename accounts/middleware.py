from django.http import Http404
import requests
from django.utils.timezone import now
from .models import UserActivityLog



from django.utils import timezone
import pytz
from .utils import get_client_ip, get_geolocation
from ipware import get_client_ip
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()



class UserActivityMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capture the user’s initial authenticated status
        was_authenticated = request.user.is_authenticated
        response = self.get_response(request)
        
        # Logging for Page Visit if user is authenticated
        if request.user.is_authenticated:
            ip_address = get_client_ip(request)
            location = get_geolocation(ip_address) if ip_address else "Unknown location"
            url_visited = request.path

            UserActivityLog.objects.create(
                user=request.user,
                ip_address=ip_address,
                attempt_type='Page Visit',
                http_status=response.status_code,
                url_visited=url_visited,
                location=location,
                timestamp=now()
            )
        
        # Login attempt logging
        if request.method == 'POST' and request.path == '/login/':
            ip_address = get_client_ip(request)
            location = get_geolocation(ip_address)
            attempted_username = request.POST.get('username', None)

            # Try to fetch user based on username provided in the login attempt
            try:
                user = User.objects.get(username=attempted_username)
            except User.DoesNotExist:
                user = None

            # Determine if the login was successful
            if not was_authenticated and request.user.is_authenticated:
                # Successful login
                attempt_type = 'Logged In'
                http_status = '200 OK'
            else:
                # Failed login attempt
                attempt_type = 'Failed to Log In'
                http_status = '401 Unauthorized'

            # Log the attempt (success or failure)
            UserActivityLog.objects.create(
                user=user,
                ip_address=ip_address,
                attempt_type=attempt_type,
                http_status=http_status,
                url_visited=request.path,
                location=location,
            )

        # Logout attempt logging
        elif request.method == 'GET' and request.path == '/logout/':
            if request.user.is_authenticated:
                ip_address = get_client_ip(request)
                location = get_geolocation(ip_address)
                UserActivityLog.objects.create(
                    user=request.user,
                    ip_address=ip_address,
                    attempt_type="Logged Out",
                    http_status="200 OK",
                    url_visited=request.path,
                    location=location,
                )

        return response
        
class TimezoneMiddleware_:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the timezone is stored in cookies
        tzname = request.COOKIES.get('timezone')
        if tzname:
            try:
                # Activate the user's timezone
                timezone.activate(pytz.timezone(tzname))
            except pytz.UnknownTimeZoneError:
                # If timezone is unknown, fallback to default (Turkey's time)
                timezone.activate(pytz.timezone('Europe/Istanbul'))
        else:
            # Deactivate timezone, use default one (from settings.py)
            timezone.activate(pytz.timezone('Europe/Istanbul'))
        
        response = self.get_response(request)
        return response