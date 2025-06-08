"""
ASGI config for GWM project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GWM.settings')

application = get_asgi_application()

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import main.routing  # substitua "main" pelo nome real do seu app se for diferente

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GWM.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            main.routing.websocket_urlpatterns  # CORRIGIDO aqui: estava 'routingrouting'
        )
    ),
})
