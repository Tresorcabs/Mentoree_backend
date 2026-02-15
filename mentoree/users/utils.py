from allauth.account.models import EmailAddress, EmailConfirmation

def get_confirmation_url(request, user):
    email_address = EmailAddress.objects.get(user=user, email=user.email)
    confirmation = EmailConfirmation.create(email_address)
    confirmation.save()
    return confirmation.get_confirmation_url(request, email_address)