from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from users.models import CustomUser


def send_mentorship_request_email(request_id: int, email_type: str):
    """
    Send email notification for mentorship request events.

    Args:
        request_id: ID of the mentorship request
        email_type: Type of email ('created', 'accepted', 'rejected')
    """
    from profiles.models import MentorshipRequest, MentorProfile

    try:
        request = MentorshipRequest.objects.select_related(
            'mentee', 'mentor__user'
        ).get(id=request_id)

        mentor = request.mentor
        mentee = request.mentee

        # Prepare context for email template
        context = {
            'mentor_name': f"{mentor.user.first_name} {mentor.user.last_name}",
            'mentee_name': f"{mentee.first_name} {mentee.last_name}",
            'expertise': ', '.join(mentor.expertise) if mentor.expertise else 'Non spécifié',
            'duration': request.duration or 'Non spécifié',
            'objectives': request.objectives or 'Non spécifié',
            'message': request.message,
            'request_date': request.created_at.strftime('%d/%m/%Y à %H:%M'),
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'mentors_url': f"{settings.FRONTEND_URL}/mentors",
        }

        if email_type == 'created':
            # Send email to mentor
            subject = f"Nouvelle demande de mentorat de {mentee.first_name} {mentee.last_name}"
            template = 'emails/mentorship_request_created.html'
            recipient_email = mentor.user.email

        elif email_type == 'accepted':
            # Send email to mentee
            subject = f"🎉 Votre demande de mentorat a été acceptée !"
            template = 'emails/mentorship_request_accepted.html'
            recipient_email = mentee.email
            context['acceptance_date'] = timezone.now().strftime('%d/%m/%Y à %H:%M')

        elif email_type == 'rejected':
            # Send email to mentee
            subject = f"Mise à jour de votre demande de mentorat"
            template = 'emails/mentorship_request_rejected.html'
            recipient_email = mentee.email
            context['response_date'] = timezone.now().strftime('%d/%m/%Y à %H:%M')

        else:
            return False

        # Render email template
        html_message = render_to_string(template, context)

        # Send email
        send_mail(
            subject=subject,
            message='',  # Plain text version (could be added later)
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Error sending mentorship email: {e}")
        return False


def send_welcome_email(user: CustomUser):
    """
    Send welcome email to new users.

    Args:
        user: CustomUser instance
    """
    try:
        context = {
            'user_name': f"{user.first_name} {user.last_name}",
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
        }

        html_message = render_to_string('emails/welcome.html', context)

        send_mail(
            subject="Bienvenue sur Mentoree !",
            message='',
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False


def send_password_reset_email(user: CustomUser, reset_token: str):
    """
    Send password reset email.

    Args:
        user: CustomUser instance
        reset_token: Password reset token
    """
    try:
        context = {
            'user_name': f"{user.first_name} {user.last_name}",
            'reset_url': f"{settings.FRONTEND_URL}/reset-password/{reset_token}",
        }

        html_message = render_to_string('emails/password_reset.html', context)

        send_mail(
            subject="Réinitialisation de votre mot de passe",
            message='',
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return True

    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False