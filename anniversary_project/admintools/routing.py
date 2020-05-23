from django.urls import re_path

from .consumers import AdminHomeConsoleConsumer

websocket_urlpatterns = [
    re_path(r'ws/admintools-home-console/$', AdminHomeConsoleConsumer),
]
