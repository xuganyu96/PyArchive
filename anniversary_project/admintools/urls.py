from django.urls import path

from .views import home, detail, develop, delete, deployment_home, deployment_create, deployment_delete_confirm, deployment_system_log

urlpatterns = [
    path('', home, name='admintools-home'),
    path('tool/<tool_id>/', detail, name='admintools-detail'),
    path('tool/<tool_id>/delete', delete, name='admintools-delete'),
    path('develop/', develop, name='admintools-develop'),
    path('deployment/', deployment_home, name='admintools-deploy'),
    path('deployment/create', deployment_create, name='admintools-deploy-create'),
    path('deployment/delete/<int:pk>', deployment_delete_confirm, name='admintools-deploy-delete'),
    path('system_log/', deployment_system_log, name='admintools-system-log'),
]