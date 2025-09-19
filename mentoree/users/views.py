import json
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from .serializers import CustomUserSerializer
from users.models import CustomUser
from allauth.account.views import ConfirmEmailView
from .signals import send_custom_confirmation_email
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model, authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken, RefreshToken
import secrets  # Importer le module secrets pour générer des clés sécurisées
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ========== Vue pour activer le compte =====================

def activate_account(request, activation_key):
    User = get_user_model()
    try:
        user = User.objects.get(activation_key=activation_key)
        user.is_active = True
        user.save()
        return HttpResponse("Votre compte a été activé avec succès.")
    except ObjectDoesNotExist:
        return HttpResponse("Le lien d'activation est invalide ou a expiré.", status=400)

# ===========================================================

# Fontion pour la creation de compte
#def register




# ========== Vue pour la gestion des utilisateurs =====================
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

# ======================================================================

# ========== Vue pour la création de compte =====================

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
        print(f'Error during account creation: {str(e)}')
        return JsonResponse({'message': str(e)}, status=500)

# ====================================================================== 

# ========== Fonction pour générer une clé d'activation aléatoire ================================
def generate_activation_key():
    return secrets.token_urlsafe(20)  # Génère une clé d'activation aléatoire de 20 caractères

# ====================================================================== 

# ========== Vue pour activer le compte ================================
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
        
        # Redirection vers la page de complétion du profil
        return HttpResponseRedirect("http://localhost:5173/profile-completion")
    except ObjectDoesNotExist:
        return JsonResponse({'error': "Le lien d'activation est invalide ou a expiré."}, status=400)
    
# ====================================================================== 

# ========== Vue pour la connexion ===============================================================
@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email')
            password = data.get('password')

            # ATTENTION : adapter selon ton backend (email vs username)
            user = authenticate(request, email=email, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_active': user.is_active,
                    }
                }, status=200)
            else:
                return JsonResponse({'message': 'Identifiants incorrects'}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
#================================================================================================

#========== Fonction pour valider le token JWT ==============================================================
def validate_token(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    try:
        refresh_token = RefreshToken(token)
        refresh_token.blacklist()
        return True
    except:
        return False
    
# ====================================================================== 

# ========== Vue pour la déconnexion ==============================================================
def logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Vous êtes maintenant déconnecté'}, status=200)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
#==========================================================================================
    
# ========== Vue pour récupérer les informations de l'utilisateur connecté ===============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    try:
        """
        Retourne les infos de l'utilisateur connecté.
        Nécessite un token JWT valide dans l'en-tête Authorization.
        """
        user = request.user  # DRF a déjà identifié l'user via le token
        print(f'user : {user}')
        serializer = CustomUserSerializer(user)
        return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_profile_complete": user.is_profile_complete,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_of_birth": user.date_of_birth,
                "bio": user.bio,
                "city": user.city,
                "profile_picture": user.profile_picture if user.profile_picture else None,
                "phone": user.phone,
                "role": user.role,
            })
    except Exception as e:
        return print(f'Error fetching current user: {str(e)}')
#==========================================================================================

#========== Vue pour mettre à jour les informations de l'utilisateur connecté =============================
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_current_user(request):
    if request.method == 'PATCH':
        user = request.user
        if user.is_authenticated:
            try:
                # Handle FormData (multipart/form-data)
                data = {}

                # Extract text fields from FormData
                for key in request.POST:
                    if key.endswith('[]'):  # Handle arrays
                        array_key = key[:-2]  # Remove []
                        if array_key not in data:
                            data[array_key] = []
                        data[array_key].append(request.POST[key])
                    else:
                        data[key] = request.POST[key]

                # Process arrays from request.POST.getlist
                for key in request.POST:
                    if key.endswith('[]'):
                        array_key = key[:-2]
                        data[array_key] = request.POST.getlist(key)

                # Handle files (if any)
                if 'cv' in request.FILES:
                    # For now, we'll skip CV handling as it's not in the model
                    pass

                print("Received update data:", data)

                # Update user fields
                user_fields = ['first_name', 'last_name', 'phone', 'city', 'bio', 'date_of_birth', 'education_level', 'profile_picture']
                user_data = {k: v for k, v in data.items() if k in user_fields}

                if user_data:
                    serializer = CustomUserSerializer(user, data=user_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        return JsonResponse(serializer.errors, status=400)

                # Handle role-specific profiles
                if user.role == 'mentor' and 'expertise' in data:
                    from profiles.models import MentorProfile
                    profile, created = MentorProfile.objects.get_or_create(user=user)

                    # Ensure expertise is a list
                    if isinstance(data['expertise'], list):
                        profile.expertise = data['expertise']
                    else:
                        profile.expertise = [data['expertise']]

                    profile.save()

                elif user.role == 'mentee' and 'interests' in data:
                    from profiles.models import MenteeProfile
                    profile, created = MenteeProfile.objects.get_or_create(user=user)

                    # Ensure interests is a list
                    if isinstance(data['interests'], list):
                        profile.interests = data['interests']
                    else:
                        profile.interests = [data['interests']]

                    profile.save()

                # Return updated user data
                serializer = CustomUserSerializer(user)
                return JsonResponse(serializer.data, status=200)

            except Exception as e:
                print(f'Error in update_current_user: {str(e)}')
                return JsonResponse({'error': str(e)}, status=400)
        else:
            return JsonResponse({'message': 'Utilisateur non authentifié'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
    
# ====================================================================== 

# ========== Vue pour supprimer l'utilisateur connecté =====================
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
    
# ====================================================================== 

# ========== Vue pour changer le mot de passe de l'utilisateur connecté =====================
def change_password(request):
    if request.method == 'POST':
        user = request.user
        if user.is_authenticated:   # Vérifie si l'utilisateur est authentifié (is_a est un attribut par défaut de Django)
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
    
# ====================================================================== 

# ========== Vue pour récupérer la liste des utilisateurs (pour les administrateurs) =====================
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

# ====================================================================== 

# ========== Vue pour compléter le profil de l'utilisateur connecté et marquer le profil comme complet si toutes les données requises sont fournies =====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    user = request.user
    try:
        try:
            # Handle FormData
            data = {}

            # Extract text fields from FormData
            for key in request.POST:
                if key.endswith('[]'):  # Handle arrays
                    array_key = key[:-2]  # Remove []
                    if array_key not in data:
                        data[array_key] = []
                    data[array_key].append(request.POST[key])
                else:
                    data[key] = request.POST[key]
            
            # Process arrays from request.POST.getlist
            for key in request.POST:
                if key.endswith('[]'):
                    array_key = key[:-2]
                    data[array_key] = request.POST.getlist(key)

            # Handle files
            if 'cv' in request.FILES:
                # For now, we'll skip CV handling as it's not in the model
                pass

            print("Received data:", data)

            # Update CustomUser fields
            user_fields = ['date_of_birth', 'bio', 'education_level', 'profile_picture']
            user_data = {k: v for k, v in data.items() if k in user_fields}

            if user_data:
                serializer = CustomUserSerializer(user, data=user_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return JsonResponse(serializer.errors, status=400)

            # Handle role-specific profiles
            if user.role == 'mentor' and 'expertise' in data:
                from profiles.models import MentorProfile
                profile, created = MentorProfile.objects.get_or_create(user=user)
                
                # Ensure expertise is a list
                if isinstance(data['expertise'], list):
                    profile.expertise = data['expertise']
                else:
                    profile.expertise = [data['expertise']]
                    
                profile.save()

            elif user.role == 'mentee' and 'interests' in data:
                from profiles.models import MenteeProfile
                profile, created = MenteeProfile.objects.get_or_create(user=user)
                
                # Ensure interests is a list
                if isinstance(data['interests'], list):
                    profile.interests = data['interests']
                else:
                    profile.interests = [data['interests']]
                    
                profile.save()

            # Check if profile is complete (simplified check)
            required_fields = ['date_of_birth', 'bio', 'profile_picture']
            is_complete = all(getattr(user, field) for field in required_fields if field != 'profile_picture' or user.profile_picture)
            user.is_profile_complete = is_complete
            user.save()

            # Return updated user data
            serializer = CustomUserSerializer(user)
            return JsonResponse(serializer.data, status=200)

        except Exception as e:
            print(f'Error in complete_profile: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)

    except Exception as e:
        print(f'Error in complete_profile: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)
# ======================================================================

# ========== Vue pour vérifier si le profil de l'utilisateur est completen précisant ce qui manque =====================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def is_profile_complete(request):
    if request.method == 'GET':
        user = request.user
        if user.is_authenticated:
            required_fields = ['first_name', 'last_name', 'date_of_birth', 'bio', 'city', 'profile_picture']
            missing_fields = [field for field in required_fields if not getattr(user, field)]
            is_complete = len(missing_fields) == 0  # Le profil est complet si aucune donnée requise n'est manquante
            return JsonResponse({'is_profile_complete': is_complete, 'missing_fields': missing_fields}, status=200)
        else:
            return JsonResponse({'message': 'Utilisateur non authentifié'}, status=401)
    else:
        return JsonResponse({'message': 'Méthode non autorisée'}, status=405)
# ====================================================================== 


# =========== Vue pour récupérer tous les mentors ==========================================
