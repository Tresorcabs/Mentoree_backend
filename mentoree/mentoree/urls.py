"""
URL configuration for mentoree project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from allauth.account.models import EmailAddress
from django.core.mail import send_mail
from django.template.loader import render_to_string
from users.utils import get_confirmation_url
from users.signals import send_custom_confirmation_email
def account_inactive(request):
    return HttpResponse("Your account is inactive. Please contact support.", status=403)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),  # Authentification API
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),  # Registration
    path('accounts/inactive/', account_inactive, name='account_inactive'),
    path('api/', include('users.urls')),  # Inclut les routes de l'application users
]
