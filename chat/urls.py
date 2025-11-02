from django.urls import path
from . import views

# Define um namespace para evitar conflitos de nomes de URL
app_name = 'chat'

urlpatterns = [
    # Rota da API para gerar respostas
    path('gerar/', views.gerar_resposta_view, name='gerar_resposta'),
    
    # Rota para a lista de histórico (com paginação e filtros)
    path('historico/', views.historico_view, name='historico'),
    
    # Rota para ver um chat específico
    path('historico/<str:chat_id>/', views.chat_detail_view, name='chat_detalhe'),

    # --- NOVA ROTA PARA EXPORTAÇÃO ---
    # Captura o tipo de formato (csv ou json) pela URL
    path('exportar/<str:format_type>/', views.exportar_historico_view, name='exportar_historico'),
]

