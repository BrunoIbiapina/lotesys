from django.urls import path
from . import views

app_name = 'perguntas'

urlpatterns = [
    path('', views.lista_perguntas, name='lista'),
    path('nova/', views.nova_pergunta, name='nova'),
    path('minhas/', views.minhas_perguntas, name='minhas'),
    path('categoria/<int:categoria_id>/', views.categoria_perguntas, name='categoria'),
    path('<int:pk>/', views.detalhes_pergunta, name='detalhes'),
]