from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import api_views

urlpatterns = [
    path('login/', obtain_auth_token, name='api-login'),
    path('register/', api_views.RegisterView.as_view(), name='api-register'),
    path('profile/', api_views.ProfileView.as_view(), name='api-profile'),
]
