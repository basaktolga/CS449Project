import requests

def get_ip_reputation(ip_address):
    api_key = "e8be876d469e663bea2f363f30c5bbd497d03fe6768489b63baf8195bd4352cc"
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"
    headers = {"x-apikey": api_key}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def get_client_ip(request):
        """ Get the client IP address from the request headers """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  # Take the first IP in the list
        else:
            ip = request.META.get('REMOTE_ADDR')  # Use remote address if no X-Forwarded-For header
        return ip

def get_geolocation(ip):
    # Use a free or paid geolocation API
    api_url = f"http://ipinfo.io/{ip}/json"
    try:
        response = requests.get(api_url)
        data = response.json()
        return f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
    except Exception:
        return "Unknown location"