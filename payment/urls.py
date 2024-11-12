from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "payment"

urlpatterns = [
    path('billing/', views.billing_view, name='billing'),
    path('faucet/<int:points>/', views.faucet_points, name='faucet_points'),
]