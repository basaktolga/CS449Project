from django.urls import path, include

urlpatterns = [
    # ... other patterns ...
    path('education/', include('education.urls')),
] 