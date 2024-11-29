from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from .models import *
from accounts.models import *
from education.models import *
from django.db.models.signals import post_save
import requests
from .utils import get_ip_reputation
import csv
from django.http import HttpResponse
from django.dispatch import receiver
from education.models import Certificate, UserCertificate
from .forms import UserCertificateForm
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse


# Inline for Profile in User Admin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend the User admin to include the Profile
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')

# Register the custom user admin
admin.site.unregister(User)  # Unregister the default User admin
admin.site.register(User, CustomUserAdmin)  # Register the custom User admin

# Register Badge model with customization
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'issued_date', 'expiration_date', 'issued_by', 'image')
    search_fields = ('name', 'issued_by')
    list_filter = ('issued_date', 'expiration_date')
"""
# Register Certificate model with customization
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'issued_date', 'expiration_date', 'issued_by', 'certificate_id', 'image')
    search_fields = ('name', 'issued_by')
    list_filter = ('issued_date', 'expiration_date')
"""





"""
class UserCertificateInline(admin.TabularInline):
    model = UserCertificate
    form = UserCertificateForm
    extra = 1  # Show one extra form by default
"""

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'issued_date', 'expiration_date', 'issued_by')
    search_fields = ('name', 'issued_by')
    list_filter = ('issued_date', 'expiration_date')

    



@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'certificate', 'user_certificate_id', 'start_date', 'expiration_date', 'status', 'issued_date')
    search_fields = ('user__username', 'certificate__name', 'user_certificate_id')
    list_filter = ('status', 'start_date', 'expiration_date')

    




"""

@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'certificate', 'user_certificate_id', 'start_date', 'expiration_date', 'status', 'issued_date')

    def get_queryset(self, request):
        # This ensures that only users with certificates are displayed
        queryset = super().get_queryset(request)
        return queryset.filter(user__usercertificate__isnull=False).distinct()

    def user_link(self, obj):
        # This will display the user as a clickable link
        return format_html('<a href="/admin/education/usercertificate/?user__id={}">{}</a>', obj.user.id, obj.user.username)
    
    user_link.short_description = 'User'  # Column name for User

    search_fields = ('user__username', 'certificate__name', 'user_certificate_id')
    list_filter = ('status', 'start_date', 'expiration_date')
"""
# Register Tag model
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Register Lecturer model
@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'difficulty', 'points', 'total_contents', 'lecturer', 'is_active', 'enrollment_count')
    search_fields = ('name', 'description', 'lecturer__name')
    list_filter = ('difficulty', 'is_active', 'lecturer')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress', 'date_enrolled')
    search_fields = ('user__username', 'course__name')
    list_filter = ('course', 'progress')

# Register Profile model if you want to manage it directly (optional)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'location', 'points', 'created_at', 'updated_at')
    search_fields = ('user__username', 'bio', 'location')

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'has_video')
    search_fields = ('title', 'course__name')
    list_filter = ('course', 'has_video')
    ordering = ('order',)

    # Optional inline to manage content completion if needed
    class ContentCompletionInline(admin.TabularInline):
        model = Content.completed_by.through
        extra = 0  # Show no empty rows by default

    inlines = [ContentCompletionInline]

class TicketAdminForm(forms.ModelForm):
    response_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}), required=False)

    class Meta:
        model = Ticket
        fields = '__all__'
        exclude = ('responses',)  # Exclude responses from being edited directly in the form

class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = ('user', 'title', 'category', 'status', 'topic', 'attachment' ,'date_updated', )
    search_fields = ('user__username', 'title', 'status', 'topic')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # If object exists (i.e., it's not a new object)
            return ('date_created', 'date_updated', 'topic', 'responses')
        return ('date_created', 'date_updated')
    """
    def save_model(self, request, obj, form, change):
        if change:  # If the object is being changed (not created)
            response_text = form.cleaned_data.get('response_text')
            if response_text:
                username = request.user.username  # Get the username
                timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                if obj.responses:
                    #obj.responses += f'\n\n<strong>{username}: {response_text} - {timestamp}'
                    obj.responses += f'{username}: {response_text} - {timestamp}'
                else:
                    #obj.responses = f'<strong>{username}: {response_text} - {timestamp}' 
                    obj.responses = f'{username}: {response_text} - {timestamp}' 
        super().save_model(request, obj, form, change)
    """
    def save_model(self, request, obj, form, change):
        if 'response_text' in form.cleaned_data and form.cleaned_data['response_text']:
            response_message = form.cleaned_data['response_text']
            new_response = f"{request.user.username}: {response_message} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            obj.responses = (obj.responses or '') + new_response
            form.cleaned_data['response_text'] = ""  # Clear response_text after saving
        super().save_model(request, obj, form, change)


    def display_responses(self, obj):
        if obj.responses:
            return format_html('<div style="white-space: pre-line;">{}</div>', obj.responses)
        return "No responses yet."
    display_responses.short_description = 'Responses'

    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'status', 'topic', 'attachment', 'response_text','responses' )
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': ('date_created', 'date_updated')
        }),
    )

admin.site.register(Ticket, TicketAdmin)

class AttemptTypeFilter(admin.SimpleListFilter):
    title = 'Log Type'  # Display name for the filter in the admin panel
    parameter_name = 'log_type'  # URL parameter for this filter

    def lookups(self, request, model_admin):
        """Define filter options for admin panel dropdown."""
        return [
            ('all', 'All Logs'),
            ('auth', 'Authentication Logs'),
            ('activity', 'Activity Logs'),
        ]

    def queryset(self, request, queryset):
        """Return the filtered queryset based on selected log type."""
        # Define authentication attempt types
        auth_attempts = ['Logged In', 'Failed to Log In', 'Logged Out']
        
        if self.value() == 'auth':
            # Filter for authentication-related logs
            return queryset.filter(attempt_type__in=auth_attempts)
        elif self.value() == 'activity':
            # Filter for activity logs only, excluding authentication attempts
            return queryset.exclude(attempt_type__in=auth_attempts)
        return queryset  # Show all logs if "All Logs" is selected



@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'location', 'attempt_type', 'http_status', 'timestamp')
    #list_filter = ('attempt_type', 'http_status', )  # Filter by attempt type and HTTP status
    list_filter = (AttemptTypeFilter, 'http_status') 
    search_fields = ('user__username', 'ip_address', 'location')  # Allow searching by user, IP address, or location
    list_per_page = 10  # Display only 10 logs per page
    actions = ["export_logs_and_urls_csv", ]

    def get_queryset(self, request):
        """Return all logs for admin, but allow user-specific filtering in other views."""
        queryset = super().get_queryset(request)
        
            
        
        return queryset.exclude(attempt_type="Page Visit")

    def has_change_permission(self, request, obj=None):
        """Disable change permissions to prevent editing logs."""
        return False

    def has_add_permission(self, request):
        """Disable add permissions, logs are only created via middleware."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow admins to delete logs if needed."""
        return True

    def export_logs_and_urls_csv(self, request, queryset):
        """
        #Export logs and visited URLs to a single CSV file.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_activity_logs.csv"'
        """
        #Export logs and visited URLs to a single CSV file based on filtered logs.
        # Determine the type of logs being exported based on the applied filters
        if 'attempt_type' in request.GET:
            attempt_type = request.GET['attempt_type']
            if attempt_type == "Activity Log":
                filename = "activity_based_logs.csv"
                queryset = queryset.filter(attempt_type="Activity Log")
            elif attempt_type == "Authentication Log":
                filename = "auth_based_logs.csv"
                queryset = queryset.filter(attempt_type="Authentication Log")
            else:
                filename = "user_activity_logs.csv"  # Default for all logs
        else:
            filename = "user_activity_logs.csv"  # Default for all logs

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        # Write header for logs section
        writer.writerow(['User', 'Attempt Type', 'IP Address', 'HTTP Status', 'Location', 'Timestamp'])

        # Write log data rows
        for log in queryset:
            
            writer.writerow([
                log.user.username,
                log.attempt_type,
                log.ip_address,
                log.http_status,
                log.location,
                log.timestamp,
            ])

        # Separate section for visited URLs
        writer.writerow([])  # Empty row to separate sections
        writer.writerow(['Visited URLs', 'Timestamp'])  # Header for visited URLs section
        visited_urls = UserActivityLog.objects.filter(attempt_type="Page Visit").values('user__username', 'url_visited', 'timestamp')
        # Query all visited URLs for each user in queryset
        #visited_urls = queryset.values('user__username', 'url_visited', 'timestamp')
        for url_entry in visited_urls:
            writer.writerow([
                url_entry['user__username'],
                url_entry['url_visited'],
                url_entry['timestamp'],
            ])

        return response

    export_logs_and_urls_csv.short_description = "Export selected logs and URLs to CSV"

    def visited_urls_display(self, obj):
        """Display visited URLs related to this log entry."""
        visited_urls = UserActivityLog.objects.filter(user=obj.user, attempt_type="Page Visit").values('url_visited', 'timestamp')
        return "<br>".join([f"{url['url_visited']} - <em>{url['timestamp']}</em>" for url in visited_urls]) if visited_urls else "No visited URLs"

    visited_urls_display.short_description = "Visited URLs"  # Column header in the admin panel

    def get_urls(self):
        """Combine custom URLs with default admin URLs."""
        urls = super().get_urls()
        return urls
   


@receiver(post_save, sender=UserActivityLog)
def analyze_ip_on_login(sender, instance, **kwargs):
    if instance.attempt_type in ["Log In", "Failed Log In"]:
        ip_data = get_ip_reputation(instance.ip_address)
        if ip_data:
            reputation_score = ip_data.get("reputation", 0)
            category = ip_data.get("category", "unknown")

            IPReputation.objects.update_or_create(
                ip_address=instance.ip_address,
                defaults={"reputation_score": reputation_score, "category": category}
            )

class IPReputationAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'reputation_score', 'category', 'location')  # Columns to display in the admin list
    list_filter = ('category',)  # Optional: add a filter by category
    search_fields = ('ip_address',)  # Optional: add search functionality for IP addresses

# Register your models here
admin.site.register(IPReputation, IPReputationAdmin)


class TrendingCourseAdmin(admin.ModelAdmin):
    list_display = ('course', 'display_order')
    ordering = ('display_order',)

admin.site.register(TrendingCourse, TrendingCourseAdmin)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Path)
class PathAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'category', 'points', 'duration')
    search_fields = ('name', 'description', 'category__name', 'specialties__name', 'job_roles__name')
    list_filter = ('difficulty', 'category', 'specialties', 'job_roles')
    filter_horizontal = ('specialties', 'job_roles', 'courses')