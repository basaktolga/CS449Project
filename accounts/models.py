from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from education.models import *

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=255)
    url_visited = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)
