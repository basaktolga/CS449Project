from django.db import models
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


@login_required
def billing_view(request):
    # Add your view logic here
    return render(request, 'billing.html')

# Function to check if the faucet is active
def is_faucet_active():
    # Implement your logic to determine if the faucet is active
    # For example, you might check a setting or a time condition
    return True  # Placeholder: Always active for demonstration


@login_required
def faucet_points(request, points):
    profile = request.user.profile
    # Check if the faucet is active
    if is_faucet_active():
        profile.add_points(points)
        messages.success(request, f"{points} points have been added to your account.")
    else:
        messages.error(request, "Faucet is currently inactive.")
    return redirect('payment:billing')  # Redirect to the billing page
