from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='archive-home'),
    path('archive/new/', views.ArchiveCreateView.as_view(), name='archive-create'),
    path('archive/<pk>/update/', views.ArchiveUpdateView.as_view(), name='archive-update'),
    path('archive/<pk>/delete/', views.ArchiveDeleteview.as_view(), name='archive-delete'),
    path('archive/<pk>/', views.ArchiveDetailView.as_view(), name='archive-detail'),
]