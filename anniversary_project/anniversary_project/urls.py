from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('backups/', include('backup_manager.urls')),
    path('admin/', admin.site.urls)
]
