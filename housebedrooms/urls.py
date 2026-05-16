from django.urls import path
from . import views

urlpatterns = [
    path('<str:house_slug>/', views.lista_dormitorios, name='lista_dormitorios'),
    path('<str:house_slug>/ranking/', views.ranking, name='ranking'),
    path('<str:house_slug>/<str:username>/', views.ver_dormitorio, name='ver_dormitorio'),
    path('<str:house_slug>/eliminar-dormitorio/<str:username>/', views.eliminar_dormitorio, name='eliminar_dormitorio'),
    path('<str:house_slug>/poner-mote/<str:username>/', views.poner_mote, name='poner_mote'),
    path('<str:house_slug>/<str:username>/guardar-estilo/', views.guardar_estilo_dormitorio, name='guardar_estilo_dormitorio'),
]
