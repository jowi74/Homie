from django.urls import path
from . import views

urlpatterns = [
    path('<str:house_slug>/', views.lista_compra, name='lista_compra'),
    path('<str:house_slug>/tienda/', views.tienda, name='tienda'),
    path('<str:house_slug>/eliminar/<int:item_id>/', views.eliminar_item, name='eliminar_item_compra'),
    path('<str:house_slug>/completar/', views.completar_compra, name='completar_compra'),
    path('<str:house_slug>/api/checksum/', views.api_shopping_checksum, name='api_shopping_checksum'),
    path('<str:house_slug>/api/store_checksum/', views.api_store_checksum, name='api_store_checksum'),
    path('<str:house_slug>/tienda/crear-recompensa/', views.crear_recompensa, name='crear_recompensa'),
    path('<str:house_slug>/tienda/canjear/<int:reward_id>/', views.canjear_recompensa, name='canjear_recompensa'),
    path('<str:house_slug>/tienda/eliminar/<int:reward_id>/', views.eliminar_recompensa, name='eliminar_recompensa'),
]
