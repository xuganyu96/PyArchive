from django.urls import path

from .views import home, detail, develop, delete

urlpatterns = [
    path('', home, name='admintools-home'),
    path('tool/<tool_id>/', detail, name='admintools-detail'),
    path('tool/<tool_id>/delete', delete, name='admintools-delete'),
    path('develop/', develop, name='admintools-develop')
]