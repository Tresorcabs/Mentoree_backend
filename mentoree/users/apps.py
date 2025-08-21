from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    def ready(self):
        # Import the signals module to ensure the signal handlers are registered
        import users.signals  # noqa: F401
        # You can also import other modules or perform other startup tasks here if needed
        print("Users app is ready and signals are registered.")