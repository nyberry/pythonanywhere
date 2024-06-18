from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('dinner/gethostname/',views.gethostname, name='gethostname')
]