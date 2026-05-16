from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('inicio/', include('houses.urls')),
    path('compra/', include('shopping.urls')),
    path('tareas/', include('housetasks.urls')),
    path('dormitorios/', include('housebedrooms.urls')),
    path('chats/', include('chats.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('', include('accounts.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
