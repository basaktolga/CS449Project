from django.dispatch import receiver
from django.db.models.signals import post_save
from . import models
from django.contrib.auth.models import User
from .models import Notification
from education.models import Course

# Signal to create user profile when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        models.Profile.objects.create(user=instance)


# Signal to save the user profile whenever the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    if created:
        users = User.objects.all()  # Notify all users, or filter as needed
        for user in users:
            Notification.objects.create(
                user=user,
                message=f"A new course '{instance.name}' has been added!"
            )