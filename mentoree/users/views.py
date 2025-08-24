import json
from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions
from .serializers import CustomUserSerializer
from users.models import CustomUser
from allauth.account.views import ConfirmEmailView
from .signals import send_custom_confirmation_email
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
import secrets  # Importer le module secrets pour générer des clés sécurisées

# Create your views here.

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def activate_account(request, activation_key):
    User = get_user_model()
    try:
        user = User.objects.get(activation_key=activation_key)
        user.is_active = True
        user.save()
        return HttpResponse("Votre compte a été activé avec succès.")
    except ObjectDoesNotExist:
        return HttpResponse("Le lien d'activation est invalide ou a expiré.", status=400)

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

#========== Vue pour la création de compte

@csrf_exempt
def register(request):
    try:
        if request.method == 'POST':
            body = request.body
            data = json.loads(body.decode('utf-8'))
            
            # print (f'Body : {body}, \n Uname_send : {data.get('username')}, Email_send : {data.get('email')}, Password_send : {data.get('password')}')
            
            # Vérifiez si la clé 'username' existe dans la requête POST
            # Définissez les champs obligatoires
            required_fields = ['username', 'email', 'password']

            # Vérifiez si tous les champs obligatoires sont présents dans la requête
            for field in required_fields:
                if field not in data:
                    return HttpResponse(f"Le champ '{field}' est obligatoire", status=400)

            # Créez l'utilisateur
            user = CustomUser.objects.create_user(
                **data  # ici, on utilise les données extraites de la requête POST
            )

            # Générez la clé d'activation
            activation_key = generate_activation_key()
            user.activation_key = activation_key
            user.save()

            # Envoyez l'email de confirmation
            send_custom_confirmation_email(user)

            return redirect('login')
        else:
            return render(request, 'users/register.html')
    except Exception as e:
        return HttpResponse(f"Une erreur s'est produite lors de la création du compte : {str(e)}", status=500)

#========== Fonction pour générer une clé d'activation aléatoire
def generate_activation_key():
    return secrets.token_urlsafe(20)  # Génère une clé d'activation aléatoire de 20 caractères

#========== Vue pour activer le compte
def activate_account(request, activation_key):
    try:
        # ici on récupère l'utilisateur qui correspond à la clé d'activation
        if not activation_key:
            return HttpResponse("Clé d'activation manquante.", status=400)
        user = CustomUser.objects.get(activation_key=activation_key)
        print(f'user : {user}')
        # on active l'utilisateur
        if user.is_active:
            return HttpResponse("Votre compte est déjà actif.")
        # on active l'utilisateur et on supprime la clé d'activation
        user.is_active = True
        user.activation_key = None  # Supprimer la clé d'activation après activation
        user.save()
        
        confirm_message = "Votre compte a été activé avec succès."
        # On redirige vers login avec le message de confirmation
        return JsonResponse({'message': "Votre compte a été activé avec succès."}, status=200)
    except ObjectDoesNotExist:
        return JsonResponse({'error': "Le lien d'activation est invalide ou a expiré."}, status=400)
    
#========== Vue pour la connexion
def login(request):
    return render(request, 'mentoree/login.html')