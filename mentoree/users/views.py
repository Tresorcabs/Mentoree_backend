import json
from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions
from .serializers import CustomUserSerializer
from users.models import CustomUser
from allauth.account.views import ConfirmEmailView
from .signals import send_custom_confirmation_email
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken, RefreshToken
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
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return JsonResponse({'access': str(refresh.access_token), 'refresh': str(refresh)}, status=201)
            
            return JsonResponse({'message': "Compte créé avec succès. Veuillez vérifier votre email pour activer votre compte."}, status=201)
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
        
        # On redirige vers login avec le message de confirmation
        return JsonResponse({'message': "Votre compte a été activé avec succès."}, status=200)
    except ObjectDoesNotExist:
        return JsonResponse({'error': "Le lien d'activation est invalide ou a expiré."}, status=400)
    
#========== 
#========== Vue pour la connexion
@csrf_exempt
def login(request):
    if request.method == 'POST':
        body = request.body
        data = json.loads(body.decode('utf-8'))
        email = data.get('email')
        password = data.get('password')
        user = authenticate(request, email=email, password=password)
        print(f'user : {user}')
        if user is not None:
            refresh = RefreshToken.for_user(user)
            print(f"user token : {refresh}")
            return JsonResponse({'access': str(refresh.access_token), 'refresh': str(refresh)}, status=200)
        else:
            return JsonResponse({'message': 'Identifiants incorrects'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
#==========

#========== Fonction pour valider le token JWT
def validate_token(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    try:
        refresh_token = RefreshToken(token)
        refresh_token.blacklist()
        return True
    except:
        return False
    
#==========
#========== Vue pour la déconnexion
def logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Vous êtes maintenant déconnecté'}, status=200)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
    
#========== Vue pour récupérer les informations de l'utilisateur connecté
def get_current_user(request):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            serializer = CustomUserSerializer(user)
            return JsonResponse(serializer.data, status=200)
        else:
            return JsonResponse({'message': 'Utilisateur non authentifié'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
    
#========== Vue pour mettre à jour les informations de l'utilisateur connecté
def update_current_user(request):
    if request.method == 'PUT':
        user = request.user
        if user.is_authenticated:
            body = request.body
            data = json.loads(body.decode('utf-8'))
            serializer = CustomUserSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, status=200)
            else:
                return JsonResponse(serializer.errors, status=400)
        else:
            return JsonResponse({'message': 'Utilisateur non authentifié'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
    
#========== Vue pour supprimer l'utilisateur connecté
def delete_current_user(request):
    if request.method == 'DELETE':
        user = request.user
        if user.is_authenticated:
            user.delete()
            return JsonResponse({'message': 'Utilisateur supprimé avec succès'}, status=200)
        else:
            return JsonResponse({'message': 'Utilisateur non authentifié'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
    
#========== Vue pour changer le mot de passe de l'utilisateur connecté
def change_password(request):
    if request.method == 'POST':
        user = request.user
        if user.is_authenticated:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return JsonResponse({'message': 'Mot de passe changé avec succès'}, status=200)
            else:
                return JsonResponse({'message': 'Ancien mot de passe incorrect'}, status=400)
        else:
            return JsonResponse({'message': 'Utilisateur non authentifié'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
    
#========== Vue pour récupérer la liste des utilisateurs (pour les administrateurs)
def list_users(request):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated and user.is_staff:
            users = CustomUser.objects.all()
            serializer = CustomUserSerializer(users, many=True)
            return JsonResponse(serializer.data, safe=False, status=200)
        else:
            return JsonResponse({'message': 'Accès interdit'}, status=403)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)