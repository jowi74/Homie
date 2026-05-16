from django.urls import path
from . import views

urlpatterns = [
    path('<str:house_slug>/', views.chat_index, name='chat_index'),
]
