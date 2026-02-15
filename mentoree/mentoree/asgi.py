"""
ASGI config for mentoree project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""
# mentoree/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mentoree.settings')
django.setup()  # <-- Important : init Django avant d'importer ton app

import messaging.routing  # après django.setup()
from messaging.consumers import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            messaging.routing.websocket_urlpatterns
        )
    ),
})

