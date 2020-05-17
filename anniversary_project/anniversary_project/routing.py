from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import admintools.routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(URLRouter(admintools.routing.websocket_urlpatterns)),
})
