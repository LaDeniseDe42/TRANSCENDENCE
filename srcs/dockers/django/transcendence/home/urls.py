from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index/<str:goto>/', views.index2, name='index2'),
    path('navbar/', views.navbar, name='navbar'),
    path('home/', views.home, name='home'),
]