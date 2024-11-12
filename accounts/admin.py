from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from .models import *
from accounts.models import *
from education.models import *

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

# Register Certificate model with customization
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'issued_date', 'expiration_date', 'issued_by', 'image')
    search_fields = ('name', 'issued_by')
    list_filter = ('issued_date', 'expiration_date')

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

@admin.register(Path)
class PathAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'type', 'lessons', 'duration', 'points')
    search_fields = ('name', 'description', 'type')
    list_filter = ('difficulty', 'type')

class TicketAdminForm(forms.ModelForm):
    #response_text = forms.CharField(widget=forms.Textarea, required=False, label='Admin Response')
    #response_text = forms.CharField(widget=forms.Textarea, required=False, label='Admin Response', max_length=None)
    response_text = models.TextField(blank=True, null=True)  

    class Meta:
        model = Ticket
        fields = '__all__'
        exclude = ('responses',)  # Exclude responses from being edited directly in the form

class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = ('user', 'title', 'status', 'topic', 'date_updated')
    search_fields = ('user__username', 'title', 'status', 'topic')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # If object exists (i.e., it's not a new object)
            return ('date_created', 'date_updated', 'topic', 'responses')
        return ('date_created', 'date_updated')

    def save_model(self, request, obj, form, change):
        if change:  # If the object is being changed (not created)
            response_text = form.cleaned_data.get('response_text')
            if response_text:
                username = request.user.username  # Get the username
                # Append the new response
                if obj.responses:
                    obj.responses += f'\n\n<strong>{username}: {response_text} - {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'  # Removed (Admin) from here
                else:
                    obj.responses = f'<strong>{username}: {response_text}'  # Removed (Admin) from here
        super().save_model(request, obj, form, change)

    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'status', 'topic', 'attachment' ,'responses', 'response_text')
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': ('date_created', 'date_updated')
        }),
    )

admin.site.register(Ticket, TicketAdmin)