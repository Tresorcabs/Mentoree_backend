from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from .views import register, activate_account, login

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
]
