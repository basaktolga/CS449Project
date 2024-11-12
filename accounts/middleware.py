from django.http import Http404
import requests
from django.utils.timezone import now
from .models import UserActivityLog


class UserActivityMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            ip_address = self.get_client_ip(request)
            location = self.get_location(ip_address)  # You can implement a service to get location.
            url_visited = request.path
            
            UserActivityLog.objects.create(
                user=request.user,
                ip_address=ip_address,
                location=location,
                url_visited=url_visited,
                timestamp=now()
            )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_location(self, ip_address):
        try:
            response = requests.get(f'https://ipinfo.io/{ip_address}/json')
            data = response.json()
            return data.get('city', 'Unknown') + ', ' + data.get('region', 'Unknown')
        except requests.RequestException:
            return 'Unknown'
