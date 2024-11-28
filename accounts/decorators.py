from django.core.cache import cache
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from datetime import datetime, timedelta

def rate_limit_verification_codes(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.user.id
        cache_key = f'verification_codes_{user_id}'
        
        # Get the list of timestamps from cache
        attempts = cache.get(cache_key, [])
        current_time = datetime.now()
        
        # Filter out attempts older than 30 minutes
        valid_attempts = [
            timestamp for timestamp in attempts 
            if current_time - timestamp < timedelta(minutes=30)
        ]
        
        if len(valid_attempts) >= 5:
            messages.error(
                request, 
                "Too many verification code requests. Please wait before requesting another code.",
                extra_tags='error settings-related'
            )
            return redirect('accounts:settings')
        
        # Add current attempt
        valid_attempts.append(current_time)
        
        # Update cache with new list of attempts
        cache.set(cache_key, valid_attempts, timeout=1800)  # 30 minutes
        
        return view_func(request, *args, **kwargs)
    return wrapper 