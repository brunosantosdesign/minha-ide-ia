from django.contrib import admin
from django.urls import path, include
# Volta a ser simples
from core.views import index_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='index'),
    path('chat/', include('chat.urls')),
]