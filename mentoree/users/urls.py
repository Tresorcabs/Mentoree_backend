from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from .views import register, activate_account, login, logout, validate_token, get_current_user, update_current_user, delete_current_user, change_password

router = DefaultRouter()  # Crée un routeur pour gérer les routes de l'API
# Enregistre le UserViewSet avec le routeur
# Cela permet de créer automatiquement les routes pour les opérations CRUD sur les utilisateurs
# Le préfixe 'users' sera utilisé pour accéder à ces routes
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)), # Inclut les routes du routeur dans les URL de l'application
    path('register/', register, name='register'),  # Route pour la création de compte   
    path('account/activate/<str:activation_key>/', activate_account, name='activate_account'),  # Route pour l'activation du compte avec une clé
    # route pour le login
    path('login/', login, name='login'),  # Route pour la connexion
    path('logout/', logout, name='logout'),  # Route pour la déconnexion
    path('validate-token/', validate_token, name='validate_token'),  # Route pour valider le token JWT
    path('current-user/', get_current_user, name='get_current_user'),  # Route pour obtenir les informations de l'utilisateur actuel
    path('current-user/update/', update_current_user, name='update_current_user'),  # Route pour mettre à jour les informations de l'utilisateur actuel
    path('current-user/delete/', delete_current_user, name='delete_current_user'),  # Route pour supprimer l'utilisateur actuel
    path('current-user/change-password/', change_password   , name='change_password'),  # Route pour changer le mot de passe
    
]
