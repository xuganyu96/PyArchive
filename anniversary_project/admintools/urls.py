from django.urls import path

from .views import home, detail, develop, deploy

urlpatterns = [
    path('', home, name='admintools-home'),
    path('tool/<tool_id>/', detail, name='admintools-detail'),
    path('develop/', develop, name='admintools-develop'),
    path('deploy/', deploy, name='admintools-deploy'),
]