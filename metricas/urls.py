from django.urls import path

from . import views

app_name = 'metricas'

urlpatterns = [
    path('', views.painel, name='painel'),
]
