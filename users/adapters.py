from allauth.account.adapter import DefaultAccountAdapter

from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # Si c'est un serializer au lieu d'un form, on gère différemment
        if hasattr(form, 'validated_data'):
            # C'est un serializer (dj-rest-auth)
            data = form.validated_data
            user.email = data.get('email', '')
            user.username = data.get('username', '')
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            # Champs personnalisés
            user.phone = data.get('phone', '')
            user.role = data.get('role', '')
        else:
            # C'est un form classique (allauth)
            user = super().save_user(request, user, form, commit=False)
            
        if commit:
            user.save()
        return user