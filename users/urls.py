from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, CustomConfirmEmailView

router = DefaultRouter()  # Crée un routeur pour gérer les routes de l'API
# Enregistre le UserViewSet avec le routeur
# Cela permet de créer automatiquement les routes pour les opérations CRUD sur les utilisateurs
# Le préfixe 'users' sera utilisé pour accéder à ces routes
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)), # Inclut les routes du routeur dans les URL de l'application
    path('api/auth/registration/account-confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),  # Route pour le message de confirmation d'email
]
