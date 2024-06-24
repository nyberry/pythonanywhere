from django.contrib import admin
from django.urls import path
from dinner import views

urlpatterns = [
    path('', views.join_game, name='join_game'),
    path('game/<int:pk>/', views.ask_question, name='ask_question'),
    path('game/<int:pk>/guess/', views.guess, name='guess'),
    path('game/<int:pk>/spectate/', views.spectate, name='spectate'),
    path('register_player/', views.register_player, name='register_player'), 
    path('start_new_game/', views.start_new_game, name='start_new_game'),
    path('winner_page/<int:pk>', views.winner_page, name='winner_page'),
    path('loser/<int:pk>/', views.loser_page, name='loser_page'),
    path('reset_game/', views.reset_game, name='reset_game'),
]
