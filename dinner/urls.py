from django.contrib import admin
from django.urls import path
from dinner import views

urlpatterns = [
    path('', views.join_game, name='join_game'),
    path('game/<int:pk>/get_question/', views.get_question, name='get_question'),
    path('game/<int:pk>/', views.ask_question, name='ask_question'),
    path('game/<int:pk>/lobby/', views.lobby, name='lobby'),
    path('game/<int:pk>/guess/', views.guess, name='guess'),
    path('game/<int:pk>/spectate/', views.spectate, name='spectate'),
    path('game/<int:pk>/view_result/', views.view_result, name='view_result'),
    path('join/', views.register_player, name='register_player'), 
    path('log_out/', views.log_out, name='log_out'), 
    path('start_new_game/', views.start_new_game, name='start_new_game'),
    path('game/<int:pk>/winner', views.winner_page, name='winner_page'),
    path('game/<int:pk>/out', views.loser_page, name='loser_page'),
    path('reset_game/', views.reset_game, name='reset_game'),
]
