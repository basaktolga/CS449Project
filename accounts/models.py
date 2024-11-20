from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from education.models import *
from django.conf import settings
import requests
from django.utils import timezone
from datetime import timedelta
import random
import string

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    points = models.PositiveIntegerField(default=0)
    badges = models.ManyToManyField('education.Badge', blank=True)  # Updated reference
    certificates = models.ManyToManyField('education.Certificate', blank=True)  # Updated reference
    image = models.ImageField(upload_to='user_photos/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])])  # Path for storing certificate images
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def add_points(self, points):
        if points < 0:
            raise ValidationError("Points cannot be negative.")
        self.points += points
        self.save()

    def subtract_points(self, points):
        if points < 0:
            raise ValidationError("Points cannot be negative.")
        if self.points >= points:
            self.points -= points
            self.save()
            return True
        return False

    def assign_badge(self, badge):
        if not self.badges.filter(id=badge.id).exists():
            self.badges.add(badge)
            self.save()
            return True
        return False

    def remove_badge(self, badge):
        if self.badges.filter(id=badge.id).exists():
            self.badges.remove(badge)
            self.save()
            return True
        return False

    def assign_certificate(self, certificate):
        if not self.certificates.filter(id=certificate.id).exists():
            self.certificates.add(certificate)
            self.save()
            return True
        return False

    def remove_certificate(self, certificate):
        if self.certificates.filter(id=certificate.id).exists():
            self.certificates.remove(certificate)
            self.save()
            return True
        return False
    

class VerificationCode(models.Model):
    ACTION_CHOICES = [
        ('change_password', 'Change Password'),
        ('delete_account', 'Delete Account'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(null=True, blank=True)

    @classmethod
    def create_verification(cls, user, action, data=None):
        """Class method to safely create a verification code"""
        if not user.pk:
            raise ValueError("User must be saved before creating verification code")
            
        code = ''.join(random.choices(string.digits, k=6))
        verification = cls(
            user=user,
            code=code,
            action=action,
            data=data
        )
        verification.save()
        return verification

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.username} - {self.action}"
    
# Ticket model for the ticketing system
class Ticket(models.Model):

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    category = models.CharField(max_length=100, default='General')  # Default value added
    topic = models.TextField(max_length=500)
    responses = models.TextField(null=True, blank=True)  # This field stores the admin's responses
    response_text = models.TextField(blank=True, null=True)  # this is for admin to write response

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=255)
    reminder_text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class UserActivityLog(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    ip_address = models.GenericIPAddressField()
    attempt_type = models.CharField(max_length=50, default='Unknown')  
    http_status = models.CharField(max_length=50, default='200 OK')    # e.g., '200 OK' or '401 Unauthorized'
    url_visited = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)  
    location = models.CharField(max_length=255, default='Unknown')
    ticket = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True, blank=True)


class IPReputation(models.Model):
    ip_address = models.GenericIPAddressField()
    reputation_score = models.IntegerField(default=0)
    category = models.CharField(max_length=255, default="unknown")
    location = models.CharField(max_length=255, default='')



def get_ip_reputation(ip_address):
    api_key = "e8be876d469e663bea2f363f30c5bbd497d03fe6768489b63baf8195bd4352cc"
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"
    headers = {"x-apikey": api_key}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None