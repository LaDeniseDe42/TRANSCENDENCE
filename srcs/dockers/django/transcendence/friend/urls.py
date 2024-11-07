from django.contrib import admin
from django.urls import path, include
from . import views
from home.views import home

from django.contrib.auth import views as auth_views


# Rôle: Définir les routes (URL) qui pointent vers les vues.
# urls.py associe chaque URL demandée par l'utilisateur à une vue spécifique.

urlpatterns = [
    path('', views.friend, name='friend'),
    path('add_friend/', views.add_friend, name='add_friend/'),
    path('accept_friend/', views.accept_friend, name='accept_friend'),
    path('remove_friend/', views.remove_friend, name='remove_friend'),
    path('update_friend/', views.update_friend, name='update_friend'),
]