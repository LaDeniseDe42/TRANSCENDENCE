from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.game, name='game'),
    path('single/', views.single, name='single'),
    path('multi/', views.multi, name='multi'),
    path('tournament/', views.tournament, name='tournament'),
    path('remote/', views.remote, name='remote'),
    path('waiting/', views.waiting, name='waiting'),
    path('update_matchmaking_status/', views.update_matchmaking_status, name='update_matchmaking_status'),
    path('tournament/game/', views.tournamentGames, name='tournamentGames'),
    path('multi4/', views.multi4, name='multi4'),
]