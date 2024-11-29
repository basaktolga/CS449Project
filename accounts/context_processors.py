from .models import Notification
from django.contrib import messages

def notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        return {'notifications': notifications}
    return {}

def login_message_processor(request):
    storage = messages.get_messages(request)
    for message in storage:
        if not message.tags:
            message.tags = 'login'
        elif 'login' not in message.tags:
            message.tags = f'login {message.tags}'
    storage.used = False
    return {}