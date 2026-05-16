from django.urls import path
from . import views

urlpatterns = [
    path('<str:house_slug>/', views.lista_tareas, name='lista_tareas'),
    path('<str:house_slug>/completar/<int:task_id>/', views.marcar_tarea_completada, name='marcar_tarea_completada'),
    path('<str:house_slug>/deshacer/<int:task_id>/', views.deshacer_tarea, name='deshacer_tarea'),
    path('<str:house_slug>/eliminar/<int:task_id>/', views.eliminar_tarea, name='eliminar_tarea'),
    path('<str:house_slug>/api/checksum/', views.api_tasks_checksum, name='api_tasks_checksum'),
]
