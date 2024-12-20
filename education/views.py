from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import *
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from .models import Certificate
from django.http import HttpResponse
from accounts.forms import UserCertificateForm
from django.contrib import messages
from accounts.forms import CertificateValidationForm
from .models import Certificate, Content
from accounts.forms import UserCertificateForm
from accounts.forms import CertificateValidationForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
#from django_ratelimit.decorators import ratelimit

# Rate limit applied to allow 5 requests per minute per IP
#@ratelimit(key='ip', rate='5/m', method='GET', block=True)
def validate_certificate(request, certificate_id):
    try:
        certificate = get_object_or_404(Certificate, certificate_id=certificate_id)
        return render(request, 'certificate_validation.html', {'certificate': certificate})
    except Certificate.DoesNotExist:
        return HttpResponse("Invalid certificate ID", status=404)




def assign_user_certificate(request):
    if request.method == 'POST':
        form = UserCertificateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User certificate assigned successfully.')
            return redirect('some_view')  # Replace with the appropriate redirect
    else:
        form = UserCertificateForm()

    return render(request, 'accounts/assign_user_certificate.html', {'form': form})


"""

def certificate_validation(request):
    certificate = None
    valid = False  # Variable to check if certificate is valid

    if request.method == 'POST':
        # Get the form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_cert_id = request.POST.get('id_user_certification')

        # Try to find the UserCertificate by first_name, last_name, and user_cert_id
        try:
            # Filter the UserCertificate table based on provided details
            user_certificate = UserCertificate.objects.get(
                user__first_name=first_name,
                user__last_name=last_name,
                certificate__id=user_cert_id
            )
            # If found, get the associated certificate
            certificate = user_certificate.certificate
            valid = True  # Certificate is valid
        except UserCertificate.DoesNotExist:
            valid = False  # Certificate not found or invalid

    return render(request, 'certificate_validation.html', {
        'certificate': certificate,
        'valid': valid
    })
"""


def certificate_validation(request):
    certificate = None
    valid = False
    error_message = None

    if request.method == 'POST':
        # Get the form data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_cert_id_str = request.POST.get('id_user_certification')

        # Validate if the certificate ID is a valid UUID
        try:
            user_cert_id = uuid.UUID(user_cert_id_str)  # Check if the user_cert_id is a valid UUID

            # Now check for UserCertificate entry tied to the provided details (no need for user authentication)
            try:
                # Check if the combination of first_name, last_name, and user_certificate_id exists in UserCertificate
                user_certificate = UserCertificate.objects.get(
                    first_name=first_name,  # Match against first_name
                    last_name=last_name,  # Match against last_name
                    user_certificate_id=user_cert_id  # Match against user_certificate_id
                )
                certificate = user_certificate.certificate  # Retrieve the related certificate
                valid = True  # Mark as valid

            except UserCertificate.DoesNotExist:
                error_message = "Certificate not found for the given details."
                valid = False

        except ValueError:
            error_message = "The Certificate ID is not valid. Please provide a valid UUID."
            valid = False  # Invalid UUID format

    return render(request, 'certificate_validation.html', {
        'certificate': certificate,
        'valid': valid,
        'error_message': error_message
    })


"""
def certificate_detail(request, cert_id):
    certificate = get_object_or_404(Certificate, certificate_id=cert_id)
    return render(request, 'certificate_detail.html', {'certificate': certificate})
"""
def certificate_detail(request, certificate_id):
    certificate = Certificate.objects.get(id=certificate_id)
    # Assuming you have a model UserCertificate that links the certificate to the user
    user_certificate = UserCertificate.objects.get(certificate=certificate, user=request.user)
    
    return render(request, 'certificate_detail.html', {
        'certificate': certificate,
        'user_certificate': user_certificate,
    })

from django.db.models import Count

@login_required
def user_dashboard(request):
    enrolled_courses = Course.objects.filter(enrolled_users=request.user)
    
    # Get the first tag from database for now
    first_tag = Tag.objects.first()  # Assuming you have a Tag model
    recommended_courses = Course.objects.filter(tags=first_tag)[:10] if first_tag else []
    
    # Get trending courses
    trending_courses = Course.objects.filter(trendingcourse__isnull=False).order_by('trendingcourse__display_order')
    
    best_selling_courses = Course.objects.annotate(
        enrolled_count=Count('enrolled_users', distinct=True)
    ).order_by('-enrolled_count', 'name')[:10]
    
    context = {
        'enrolled_courses': enrolled_courses,
        'recommended_courses': recommended_courses,
        'recommended_tag': first_tag,
        'best_selling_courses': best_selling_courses,
        'trending_courses': trending_courses,
        'user': request.user,
    }
    return render(request, 'user_dashboard.html', context)

@login_required
def owned_courses(request):
    owned_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    query = request.GET.get('q', '').strip()
    ordering = request.GET.get('ordering', 'course_old_to_recent')
    selected_tags = request.GET.getlist('tags[]')
    difficulty = request.GET.get('difficulty', '')

    # Initial course query including owned courses
    owned_courses = Course.objects.filter(id__in=owned_ids)

    # Apply search query
    if query:
        owned_courses = owned_courses.filter(name__icontains=query)

    # Apply difficulty filter
    if difficulty:
        owned_courses = owned_courses.filter(difficulty=difficulty)

    # Apply tag filter
    if selected_tags:
        owned_courses = owned_courses.filter(tags__in=selected_tags).distinct()

    # Apply ordering
    if ordering == 'course_recent_to_old':
        owned_courses = owned_courses.order_by('-id')
    else:
        owned_courses = owned_courses.order_by('id')

    all_tags = Tag.objects.all()  # Get all available tags

    return render(request, 'owned_courses.html', {'owned_courses': owned_courses, 'all_tags': all_tags})

@login_required
def all_courses(request):
    query = request.GET.get('q', '').strip()
    ordering = request.GET.get('ordering', 'course_old_to_recent')
    selected_tags = request.GET.getlist('tags[]')
    difficulty = request.GET.get('difficulty', '')

    # Initial course query including owned courses
    all_courses = Course.objects.all()

    # Apply search query
    if query:
        all_courses = all_courses.filter(name__icontains=query)

    # Apply difficulty filter
    if difficulty:
        all_courses = all_courses.filter(difficulty=difficulty)

    # Apply tag filter
    if selected_tags:
        all_courses = all_courses.filter(tags__in=selected_tags).distinct()

    # Apply ordering
    if ordering == 'course_recent_to_old':
        all_courses = all_courses.order_by('-id')
    else:
        all_courses = all_courses.order_by('id')

    all_tags = Tag.objects.all()  # Get all available tags

    return render(request, 'all_courses.html', {'all_courses': all_courses, 'all_tags': all_tags})

@login_required
def available_courses(request):
    owned_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    query = request.GET.get('q', '').strip()
    ordering = request.GET.get('ordering', 'course_old_to_recent')
    selected_tags = request.GET.getlist('tags[]')
    difficulty = request.GET.get('difficulty', '')

    # Initial course query including owned courses
    available_courses = Course.objects.exclude(id__in=owned_ids)

    # Apply search query
    if query:
        available_courses = available_courses.filter(name__icontains=query)

    # Apply difficulty filter
    if difficulty:
        available_courses = available_courses.filter(difficulty=difficulty)

    # Apply tag filter
    if selected_tags:
        available_courses = available_courses.filter(tags__in=selected_tags).distinct()

    # Apply ordering
    if ordering == 'course_recent_to_old':
        available_courses = available_courses.order_by('-id')
    else:
        available_courses = available_courses.order_by('id')

    all_tags = Tag.objects.all()  # Get all available tags

    return render(request, 'available_courses.html', {'available_courses': available_courses, 'all_tags': all_tags})
@login_required
def filter_owned_courses(request):
    query = request.GET.get('q', '').strip().lower()  # Keeping query search logic intact
    ordering = request.GET.get('ordering', 'course_old_to_recent')
    tags = request.GET.getlist('tags[]')
    difficulty = request.GET.get('difficulty', 'course_all')

    # Fetch courses owned by the user
    owned_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    courses = Course.objects.filter(id__in=owned_ids)

    # Apply search query filter
    if query:
        courses = courses.filter(name__icontains=query)

    # Apply difficulty filter
    difficulty_map = {
        'course_easy': 'easy',
        'course_medium': 'medium',
        'course_hard': 'hard',
        'easy': 'easy',   # Allow flexibility in parameter names
        'medium': 'medium',
        'hard': 'hard',
    }
    if difficulty in difficulty_map:
        courses = courses.filter(difficulty=difficulty_map[difficulty])

    # Apply tags filter
    if tags:
        courses = courses.filter(tags__in=tags).distinct()

    # Apply ordering filter
    if ordering == 'recent_to_old':
        courses = courses.order_by('-id')
    else:
        courses = courses.order_by('id')

    # Render the course list HTML and return it as a partial
    return render(request, 'course_filter.html', {'courses': courses})

@login_required
def filter_available_courses(request):
    query = request.GET.get('q', '')
    ordering = request.GET.get('ordering', '')
    difficulty = request.GET.get('difficulty', '')
    tags = request.GET.getlist('tags', [])
    
    courses = Course.objects.all()
    
    if query:
        courses = courses.filter(name__icontains=query)
    if difficulty and difficulty != 'all':
        courses = courses.filter(difficulty=difficulty)
    if tags:
        courses = courses.filter(tags__id__in=tags).distinct()
    if ordering:
        if ordering == 'old_to_recent':
            courses = courses.order_by('created_at')
        elif ordering == 'recent_to_old':
            courses = courses.order_by('-created_at')
            
    return render(request, 'education/course_list_partial.html', {'available_courses': courses})

@login_required
def filter_courses(request):
    query = request.GET.get('q', '').strip().lower()  # Keeping query search logic intact
    ordering = request.GET.get('ordering', 'course_old_to_recent')
    tags = request.GET.getlist('tags[]')
    difficulty = request.GET.get('difficulty', 'course_all')

    # Fetch courses owned by the user
    #owned_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    courses = Course.objects.all()

    # Apply search query filter
    if query:
        courses = courses.filter(name__icontains=query)

    # Apply difficulty filter
    difficulty_map = {
        'course_easy': 'easy',
        'course_medium': 'medium',
        'course_hard': 'hard',
        'easy': 'easy',   # Allow flexibility in parameter names
        'medium': 'medium',
        'hard': 'hard',
    }
    if difficulty in difficulty_map:
        courses = courses.filter(difficulty=difficulty_map[difficulty])

    # Apply tags filter
    if tags:
        courses = courses.filter(tags__in=tags).distinct()

    # Apply ordering filter
    if ordering == 'recent_to_old':
        courses = courses.order_by('-id')
    else:
        courses = courses.order_by('id')

    # Render the course list HTML and return it as a partial
    return render(request, 'course_filter.html', {'courses': courses})


@login_required
def my_badges(request):
    # Render the dashboard template and pass the request.user object
    return render(request, 'my_badges.html', {
        'user': request.user,
    })

"""
@login_required
def my_certificates(request):
    # Render the dashboard template and pass the request.user object
    return render(request, 'my_certificates.html', {
        'user': request.user,
    })
"""

def my_certificates(request):
    # Get all UserCertificates for the logged-in user
    user_certificates = UserCertificate.objects.filter(user=request.user)
    return render(request, 'my_certificates.html', {
        'user_certificates': user_certificates
    })


def certificate_detail(request, user_certificate_id):
    # Get the certificate details using the user_certificate_id
    certificate = get_object_or_404(UserCertificate, user_certificate_id=user_certificate_id)
    return render(request, 'certificate_detail.html', {
        'certificate': certificate
    })


@login_required
def paths(request):
    paths = Path.objects.all()  # Fetch all paths from the database
    return render(request, 'paths.html', {'paths': paths})

def course_page(request, slug):
    """View for displaying a course page with summary information and an enrollment button."""
    course = get_object_or_404(Course, slug=slug)
    context = {
        'course': course
    }
    return render(request, 'course_page.html', context)


@login_required
def enroll_in_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    profile = request.user.profile

    # Check if the user is already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.warning(request, f"You are already enrolled in {course.name}.")
        return redirect('education:course_page', slug=course.slug)

    # Check if the user has enough points to enroll
    if profile.points >= course.points:
        # Subtract points and enroll the user
        profile.points -= course.points
        profile.save()
        
        # Add the user to the course's enrolled users and create an enrollment record
        course.enrolled_users.add(request.user)
        Enrollment.objects.create(user=request.user, course=course)
        
        # Increment the enrollment count
        course.enroll_student()

        messages.success(request, f"You have successfully enrolled in {course.name}.")
    else:
        messages.error(request, "You do not have enough points to enroll in this course.")

    return redirect('education:course_page', slug=course.slug)



@login_required
def enrolled_course(request, slug):
    """View for displaying detailed content for enrolled courses."""
    course = get_object_or_404(Course, slug=slug)
    if request.user not in course.enrolled_users.all():
        messages.warning(request, 'You must be enrolled in this course to view its content.')
        return redirect('education:course_page', slug=course.slug)

    context = {
        'course': course
    }
    return render(request, 'enrolled_course.html', context)

def lecturer_profile(request, lecturer_id):
    lecturer = get_object_or_404(Lecturer, id=lecturer_id)
    return render(request, 'lecturer_profile.html', {'lecturer': lecturer})


@login_required
def learning_paths(request):
    # Fetch all dynamic filter options
    categories = Category.objects.all()
    specialties = Specialty.objects.all()
    job_roles = JobRole.objects.all()
    
    # Fetch paths to display
    paths = Path.objects.all()

    return render(
        request,
        'education/learning_paths.html',
        {
            'categories': categories,
            'specialties': specialties,
            'job_roles': job_roles,
            'paths': paths,
        },
    )
    
@login_required
def filter_paths(request):
    difficulty = request.GET.get('difficulty', 'all')
    category = request.GET.get('category', 'all')
    specialty = request.GET.get('specialty', 'all')
    job_role = request.GET.get('job_role', 'all')
    
    # Start with all paths
    paths = Path.objects.all()
    
    # Apply filters if not 'all'
    if difficulty != 'all':
        paths = paths.filter(difficulty=difficulty)
    
    if category != 'all':
        # Use exact match on category name
        paths = paths.filter(category__name__iexact=category.replace('-', ' '))
    
    if specialty != 'all':
        # Use ManyToMany relationship filtering
        paths = paths.filter(specialties__name__iexact=specialty.replace('-', ' '))
    
    if job_role != 'all':
        # Use ManyToMany relationship filtering
        paths = paths.filter(job_roles__name__iexact=job_role.replace('-', ' '))
    
    return render(request, 'education/path_list_partial.html', {'paths': paths})



@login_required
def path_detail(request, path_id):
    path = get_object_or_404(Path, slug=path_id)
    return render(request, 'education/path_detail.html', {'path': path})