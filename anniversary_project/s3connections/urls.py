from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='s3-connection-home'),
    path('create/', views.create, name='s3-connection-create'),
    path('connection/<pk>/', views.detail, name='s3-connection-detail'),
    path('connection/<pk>/update/', views.S3ConnectionUpdateView.as_view(), name='s3-connection-update'),
    path('connection/<pk>/delete/', views.S3ConnectionDeleteView.as_view(), name='s3-connection-delete'),
]