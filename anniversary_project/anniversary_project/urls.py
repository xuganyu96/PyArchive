from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('archives/', include('archive.urls')),
    path('admin/', admin.site.urls),
]