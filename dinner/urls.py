from django.urls import path
from . import views
 
urlpatterns = [
    path('', views.game_list, name='game_list'),
    path('game/<int:pk>/', views.game_detail, name='game_detail'),
    path('game/<int:pk>/guess/', views.guess, name='guess'),
    path('add_question/', views.add_question, name='add_question'),
]

#"""    path('', views.welcome, name='welcome'),
#    path('dinner/gethostname/',views.gethostname, name='gethostname'),
#    path('dinner/getplayername/',views.getplayername, name='getplayername')
#]"""