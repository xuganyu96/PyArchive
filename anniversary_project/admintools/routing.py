from django.urls import re_path

from .consumers import AdminHomeConsoleConsumer, AdminDevelopConsoleConsumer

websocket_urlpatterns = [
    re_path(r'ws/admintools-home-console/$', AdminHomeConsoleConsumer),
    re_path(r'ws/admintools-develop-console/$', AdminDevelopConsoleConsumer),

]
