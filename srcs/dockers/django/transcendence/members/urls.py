from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.homeMembers, name='home_members'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile_discover, name='profile_discover'),
    path('profile/<str:user_name>/', views.profile_discover_reverse, name='profile_discover_reverse'),
    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('logout/', views.logoutSystem, name='logout'),
    path('profile_intra/', views.profile_intra, name='profile_intra'),
    path('update_profile/', views.updateProfile, name='profile_update'),
    path('check_login_status/', views.check_login_status, name='check_login_status'),
]
