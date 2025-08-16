from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import CustomUserSerializer
from users.models import CustomUser
from allauth.account.views import ConfirmEmailView

# Create your views here.



# =========================
# Fontion pour la creation de compte
#def register





class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = CustomUser.objects.all()  # Permet de récupérer tous les utilisateurs
    serializer_class = CustomUserSerializer  # Utilise le serializer défini dans users/serializers.py pour sérialiser les données
    # Permissions: seuls les utilisateurs authentifiés peuvent accéder à ces vues
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtre les utilisateurs 
        user = self.request.user
        if user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=user.id)  # Retourne uniquement l'utilisateur connecté

class CustomConfirmEmailView(ConfirmEmailView):
    """
    Custom view to handle email confirmation.
    """
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # You can add custom logic here after email confirmation if needed
        template_name = 'account/email_confirmed.html'
        return render(request, template_name, {'response': response})
        # Render a template or return a response as needed
        # This can be used to display a confirmation message or redirect the user.
        return response
    # This view can be used to handle the email confirmation process
    # and can be linked to a URL in the urls.py file.
    # It can also be customized further if needed.