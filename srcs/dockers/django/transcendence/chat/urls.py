from django.contrib import admin
from django.urls import path, include
from . import views
from home.views import home

from django.contrib.auth import views as auth_views


# Rôle: Définir les routes (URL) qui pointent vers les vues.
# urls.py associe chaque URL demandée par l'utilisateur à une vue spécifique.

urlpatterns = [
    path('', views.chat, name='chat'),
]