from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('crear/', views.crear_casa, name='crear_casa'),
    path('<str:house_slug>/', views.casa_detalle, name='casa_detalle'),
    path('<str:house_slug>/editar-nombre/', views.editar_nombre_casa, name='editar_nombre_casa'),
    path('<str:house_slug>/editar-foto/', views.editar_foto_casa, name='editar_foto_casa'),
    path('<str:house_slug>/eliminar-miembro/<str:username>/', views.eliminar_miembro_casa, name='eliminar_miembro_casa'),
    path('<str:house_slug>/anadir-miembro/', views.anadir_miembro_casa, name='anadir_miembro_casa'),
    path('<str:house_slug>/solicitar-eliminacion/', views.solicitar_eliminacion_casa, name='solicitar_eliminacion_casa'),
    path('<str:house_slug>/confirmar-eliminacion/', views.confirmar_eliminacion_casa, name='confirmar_eliminacion_casa'),
    
    # Dashboard Features
    path('<str:house_slug>/api/corcho_checksum/', views.api_corcho_checksum, name='api_corcho_checksum'),
    path('<str:house_slug>/notas/crear/', views.crear_nota, name='crear_nota'),
    path('<str:house_slug>/notas/eliminar/<int:note_id>/', views.eliminar_nota, name='eliminar_nota'),
    path('<str:house_slug>/diario/crear/', views.crear_entrada_diario, name='crear_entrada_diario'),
    # API Recodatorios
    path('<str:house_slug>/api/recordatorios/', views.api_recordatorios, name='api_recordatorios'),
    path('<str:house_slug>/api/recordatorios/crear/', views.crear_recordatorio, name='crear_recordatorio'),
    path('<str:house_slug>/api/recordatorios/eliminar/<int:reminder_id>/', views.eliminar_recordatorio, name='eliminar_recordatorio'),
    path('<str:house_slug>/api/recordatorios/marcar-leida/', views.api_marcar_recordatorio_leido, name='api_marcar_recordatorio_leido'),
    
    # CHATS
    path('<str:house_slug>/api/chats_count/', views.api_chats_count, name='api_chats_count'),
    path('<str:house_slug>/chats/', views.lista_chats, name='lista_chats'),
    path('<str:house_slug>/chats/crear-privado/', views.crear_chat_privado, name='crear_chat_privado'),
    path('<str:house_slug>/chats/crear-grupo/', views.crear_chat_grupo, name='crear_chat_grupo'),
    
    # Privados
    path('<str:house_slug>/chats/p/<str:username>/', views.chat_privado, name='chat_privado'),
    path('<str:house_slug>/chats/p/<str:username>/api/mensajes/', views.api_mensajes_chat_privado, name='api_mensajes_chat_privado'),
    path('<str:house_slug>/chats/p/<str:username>/borrar/', views.borrar_chat_privado, name='borrar_chat_privado'),
    # (Los privados no tienen ajustes de grupo, solo borrar)

    # Grupos
    path('<str:house_slug>/chats/g/<str:room_slug>/', views.chat_grupo, name='chat_grupo'),
    path('<str:house_slug>/chats/g/<str:room_slug>/api/mensajes/', views.api_mensajes_chat_grupo, name='api_mensajes_chat_grupo'),
    path('<str:house_slug>/chats/g/<str:room_slug>/ajustes/', views.chat_ajustes_grupo, name='chat_ajustes_grupo'),
    path('<str:house_slug>/chats/g/<str:room_slug>/borrar/', views.borrar_chat_grupo, name='borrar_chat_grupo'),
    path('<str:house_slug>/chats/g/<str:room_slug>/kick/<str:username>/', views.kick_miembro_grupo, name='kick_miembro_grupo'),
    path('<str:house_slug>/chats/g/<str:room_slug>/mute/<str:username>/', views.mute_miembro_grupo, name='mute_miembro_grupo'),
    path('<str:house_slug>/chats/g/<str:room_slug>/agregar/', views.agregar_miembro_grupo_view, name='agregar_miembro_grupo_view'),
    path('<str:house_slug>/chats/g/<str:room_slug>/cambiar-imagen/', views.cambiar_imagen_grupo_view, name='cambiar_imagen_grupo_view'),
    path('<str:house_slug>/chats/g/<str:room_slug>/salir/', views.salir_grupo_view, name='salir_grupo_view'),
    
    # Finanzas
    path('<str:house_slug>/finanzas/', views.finanzas, name='finanzas'),
    path('<str:house_slug>/finanzas/agregar/', views.agregar_gasto, name='agregar_gasto'),
    path('<str:house_slug>/finanzas/eliminar/<int:expense_id>/', views.eliminar_gasto, name='eliminar_gasto'),
    path('<str:house_slug>/finanzas/pagado/<int:expense_id>/', views.marcar_pagado_gasto, name='marcar_pagado_gasto'),
    
    # Calendario Interactivo
    path('<str:house_slug>/api/calendario/', views.api_obtener_eventos_mes, name='api_obtener_eventos_mes'),
    path('<str:house_slug>/calendario/agregar/', views.agregar_evento_calendario, name='agregar_evento_calendario'),
    path('<str:house_slug>/calendario/eliminar/<int:event_id>/', views.eliminar_evento_calendario, name='eliminar_evento_calendario'),

    # Logros
    path('<str:house_slug>/logros/', views.logros, name='logros'),
]

