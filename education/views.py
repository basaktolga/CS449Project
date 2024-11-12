from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import *
from django.contrib import messages

@login_required
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

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

    return render(request, 'available_courses.html', {'available_courses': owned_courses, 'all_tags': all_tags})

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
    query = request.GET.get('q', '').strip().lower()  # Keeping query search logic intact
    ordering = request.GET.get('ordering', 'course_old_to_recent')
    tags = request.GET.getlist('tags[]')
    difficulty = request.GET.get('difficulty', 'course_all')

    # Fetch courses owned by the user
    owned_ids = Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    courses = Course.objects.exclude(id__in=owned_ids)

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


@login_required
def my_certificates(request):
    # Render the dashboard template and pass the request.user object
    return render(request, 'my_certificates.html', {
        'user': request.user,
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