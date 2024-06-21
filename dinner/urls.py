from django.contrib import admin
from django.urls import path
from dinner import views

urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('game/<int:pk>/', views.game_detail, name='game_detail'),
    path('game/<int:pk>/guess/', views.guess, name='guess'),
    path('add_question/', views.add_question, name='add_question'),
    path('register_player/', views.register_player, name='register_player'), 
    path('start_new_game/', views.start_new_game, name='start_new_game'),
]