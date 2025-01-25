from django.urls import path
from . import views

urlpatterns = [
    path('', views.app_list, name='app_list'),
    path('app/add/', views.app_add, name='app_add'),
    path('app/<int:pk>/edit/', views.app_edit, name='app_edit'),
    path('app/<int:pk>/delete/', views.app_delete, name='app_delete'),
    path('list-directory/', views.list_directory, name='list_directory'),
    path('autodiscover/', views.app_autodiscover, name='app_autodiscover'),
    path('cleanup-autodiscovered/', views.cleanup_autodiscovered, name='cleanup_autodiscovered'),
] 