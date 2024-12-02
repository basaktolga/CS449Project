from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from accounts.models import *
import uuid
from django.utils.text import slugify


"""
# Certificate model to store information about certificates
class Certificate(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Unique name for each certificate
    description = models.TextField()
    issued_date = models.DateField()  # Date the certificate was issued
    expiration_date = models.DateField(null=True, blank=True)  # Optional expiration date
    issued_by = models.CharField(max_length=100)  # Who issued the certificate
    image = models.ImageField(upload_to='certificates/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])])  # Path for storing certificate images
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # Unique certificate ID for validation

    def __str__(self):
        return f"{self.name} - {self.certificate_id}"

"""
"""
class Certificate(models.Model):
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # Unique identifier for validation
    first_name = models.CharField(max_length=100, null=True)  # Allow null temporarily
    last_name = models.CharField(max_length=100, null=True)   # Allow null temporarily
    name = models.CharField(max_length=100, null=True)         # Allow null temporarily
    description = models.TextField(null=True)                  # Allow null temporarily  # Course name, for example |  name of the certificate
    #description = models.TextField()  # Certificate description
    
    issued_by = models.CharField(max_length=100)  # Issuer name
    image = models.ImageField(upload_to='certificates/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])])  # Certificate image
    issued_date = models.DateField()  # Ensure this field exists
    expiration_date = models.DateField(null=True, blank=True)  # Ensure this field exists
    
    def __str__(self):
        return f"{self.name} - {self.certificate_id}"
"""
class Certificate(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True)  # Unique name for each certificate
    description = models.TextField(null=True)
    issued_date = models.DateField()  # Date the certificate was issued
    expiration_date = models.DateField(null=True, blank=True)  # Optional expiration date
    issued_by = models.CharField(max_length=100)  # Who issued the certificate
    image = models.ImageField(upload_to='certificates/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])])  # Path for storing certificate images
    

    def __str__(self):
        return self.name
    
"""
class UserCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to User model
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE)  # Link to Certificate model
    issued_date = models.DateField()  # Date the certificate was issued to the user
    expiration_date = models.DateField(null=True, blank=True)  # Optional expiration date
    status = models.CharField(max_length=50, choices=[('active', 'Active'), ('expired', 'Expired')], default='active')

    def __str__(self):
        return f"{self.user.username} - {self.certificate.name}"
"""

class UserCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE)
    user_certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    #user_certificate_id = models.UUIDField(default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100,null=True)
    start_date = models.DateField(null=True)
    expiration_date = models.DateField(null=True)
    status = models.CharField(max_length=50, choices=(('active', 'Active'), ('expired', 'Expired')))
    issued_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.certificate.name} - {self.user.username} ({self.certificate_id})"
    

class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Ensure badge names are unique
    description = models.TextField()
    issued_date = models.DateField()  # Date the certificate was issued
    expiration_date = models.DateField(null=True, blank=True)  # Optional expiration date
    issued_by = models.CharField(max_length=100)  # Who issued the certificate
    image = models.ImageField(upload_to='badges/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])])  # Adjust the path for better organization

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Lecturer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)  # Optional field for a biography

    def __str__(self):
        return self.name

class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    name = models.CharField(max_length=100, unique=True)  # Ensure course names are unique
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    points = models.PositiveIntegerField()
    total_contents = models.PositiveIntegerField()
    tags = models.ManyToManyField('Tag', related_name='courses')
    lecturer = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True, related_name='courses')
    image = models.ImageField(upload_to='course_images/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])])
    slug = models.SlugField(max_length=100, unique=True, blank=True)  # Add slug field


    enrolled_users = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    
    # Timestamps for tracking creation and updates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional fields for better course management
    is_active = models.BooleanField(default=True)  # Field to deactivate courses if needed
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)  # Courses that must be taken first
    enrollment_count = models.PositiveIntegerField(default=0)  # Track how many students are enrolled

    def __str__(self):
        return self.name

    def enroll_student(self):
        """Increment the enrollment count when a student enrolls."""
        self.enrollment_count += 1
        self.save()

    def unenroll_student(self):
        """Decrement the enrollment count when a student unenrolls."""
        if self.enrollment_count > 0:
            self.enrollment_count -= 1
            self.save()
    
    def get_tags_list(self):
        """Return a list of tag names associated with this course."""
        return [tag.name for tag in self.tags.all()]

    def is_popular(self, threshold=10):
        """Determine if the course is popular based on enrollment count."""
        return self.enrollment_count >= threshold
    
    # Enrollment model to track user course enrollments
class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    #path = models.ForeignKey(Path, on_delete=models.CASCADE, null=True, blank=True)  # Allow null if it's optional initially
    progress = models.FloatField(default=0)  # Percentage of course completed
    date_enrolled = models.DateTimeField(auto_now_add=True)

    def update_progress(self):
        """Update the progress percentage based on completed content"""
        total_contents = self.course.total_contents
        completed_contents = ContentCompletion.objects.filter(user=self.user, content__course=self.course).count()

        if total_contents > 0:
            self.progress = (completed_contents / total_contents) * 100
        else:
            self.progress = 100  # Handle edge case where there are no contents
        self.save()

class Content(models.Model):
    course = models.ForeignKey(Course, related_name='contents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    video = models.FileField(upload_to='media/videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    has_video = models.BooleanField(default=False)
    content_data = models.JSONField(blank=True, null=True)
    #quiz = models.ForeignKey('Quiz', related_name='contents', on_delete=models.SET_NULL, null=True, blank=True)
    completed_by = models.ManyToManyField(User, through='ContentCompletion', related_name='completed_content')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"

    def complete_content(self, user):
        """Mark this content as completed for the user"""
        ContentCompletion.objects.get_or_create(content=self, user=user)

class ContentCompletion(models.Model):
    """Track content completion for each user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    date_completed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content')

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Specialty(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class JobRole(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Path(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    difficulty = models.CharField(max_length=30, choices=DIFFICULTY_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    specialties = models.ManyToManyField(Specialty, blank=True)
    job_roles = models.ManyToManyField(JobRole, blank=True)
    lessons = models.PositiveIntegerField()
    duration = models.CharField(max_length=50)  # e.g., "7 hours", "3 days", etc.
    points = models.PositiveIntegerField()  # Points required to unlock
    image = models.ImageField(upload_to='static/paths', blank=True, null=True)
    courses = models.ManyToManyField('education.Course', related_name='paths', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class TrendingCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.course.name} (Order: {self.display_order})"