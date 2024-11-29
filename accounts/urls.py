from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordChangeView, delete_account, send_ticket, close_ticket, CustomLoginView
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static
from .forms import CustomAuthenticationForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/", 
        CustomLoginView.as_view(
            template_name="login.html",
            authentication_form=CustomAuthenticationForm,
        ), 
        name="login"
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path('settings/', views.CustomPasswordChangeView.as_view(), name='settings'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('verify_action/', views.verify_action, name='verify_action'),
    path('resend_code/', views.resend_verification_code, name='resend_code'),

    #**** Ticket related section start *****
    path('send_ticket/', send_ticket, name='send_ticket'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('activity-log/', views.activity_log_view, name='activity_log'),
    path('close_ticket/<int:ticket_id>/', close_ticket, name='close_ticket'),
    #**** Ticket related section end *****

    
]

if settings.DEBUG:  # Serve uploaded files during development
    urlpatterns += static('/attachments/', document_root='attachments/')