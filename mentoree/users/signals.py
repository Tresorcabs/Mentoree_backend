# accounts/signals.py
from allauth.account.signals import email_confirmed, user_signed_up
from django.dispatch import receiver
from django.core.mail import send_mail
import django.http
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import ActivationKey, CustomUser

@receiver(email_confirmed)
def activate_user(sender, request, email_address, **kwargs):
    user = email_address.user
    if not user.is_active:
        user.is_active = True
        user.save()

@csrf_exempt
@receiver(user_signed_up)
def send_custom_confirmation_email(user, **kwargs):
    user_activation_key = CustomUser.objects.get(email=user.email).activation_key
    activation_key = user_activation_key
    subject = "Confirmez votre inscription"
    context = {
        "user": user,
        "activation_url": f"http://127.0.0.1:8000/api/account/activate/{activation_key}/",  # À adapter selon ta logique
    }
    message = render_to_string("mentoree/custom_confirmation.txt", context)
    html_message = render_to_string("mentoree/custom_confirmation.html", context)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )
    return django.http.HttpResponse("Email de confirmation envoyé.", status=200)
