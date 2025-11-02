from django.test import TestCase, Client
from django.urls import reverse
import json
from unittest.mock import patch, MagicMock # Usaremos 'patch' para simular a IA
import mongomock # Importa o mongomock
from .services import mongo_service # Importa o nosso serviço

# --- Testes Unitários para o Serviço MongoDB ---

# Usamos @patch para "substituir" a conexão real do MongoDB pela conexão "falsa" (mongomock)
# sempre que a função _connect_db for chamada dentro de mongo_service.
@patch('chat.services.mongo_service._connect_db')
class TestMongoService(TestCase):

    def setUp(self):
        # Configura o mock do cliente MongoDB
        self.mock_client = mongomock.MongoClient()
        
        # Diz ao patch para usar o nosso mock_client quando _connect_db for chamada
        # Isso efetivamente "engana" o mongo_service, fazendo-o usar o banco de dados em memória.
        def setup_mock_db(mock_connect_func):
            mongo_service.client = self.mock_client
            mongo_service.db = self.mock_client[mongo_service.settings.MONGO_DB_NAME]
            mongo_service.chats_collection = mongo_service.db["chats"]

        # O setUp é um pouco complexo, mas garante que o mock está funcionando
        # Nós não "chamamos" a função mockada, nós a "configuramos"
        # O decorador @patch já substituiu a função real
        # Aqui, estamos a usar o setUp para garantir que as variáveis globais
        # client, db, e chats_collection no mongo_service sejam o nosso mock.
        
        # Solução mais simples: Patchear as variáveis globais diretamente
        mongo_service.client = self.mock_client
        mongo_service.db = self.mock_client[mongo_service.settings.MONGO_DB_NAME]
        mongo_service.chats_collection = mongo_service.db["chats"]


    def tearDown(self):
        # Limpa o banco de dados mockado após cada teste
        self.mock_client.drop_database(mongo_service.settings.MONGO_DB_NAME)

    def test_04_create_chat(self, mock_connect_db):
        """
        Plano de Ação 4: Testa se a função create_chat realmente cria um chat.
        """
        print("Executando: Teste 4 - mongo_service.create_chat")
        
        # 1. Chama a função para criar um chat
        chat_id = mongo_service.create_chat(title="Teste de Chat")
        
        # 2. Verifica se um ID foi retornado
        self.assertIsNotNone(chat_id)
        
        # 3. Busca diretamente no banco de dados mockado
        chat_criado = mongo_service.chats_collection.find_one({"_id": mongo_service.ObjectId(chat_id)})
        
        # 4. Verifica se o chat foi encontrado e se o título está correto
        self.assertIsNotNone(chat_criado)
        self.assertEqual(chat_criado['title'], "Teste de Chat")
        self.assertEqual(len(chat_criado['messages']), 0) # Deve começar sem mensagens


# --- Testes das Views (Páginas) ---

class TestViews(TestCase):

    def setUp(self):
        # Cria um cliente de teste do Django para fazer requisições
        self.client = Client()

    def test_01_index_page_loads(self):
        """
        Plano de Ação 1: Testa se a página inicial (/) carrega (status 200).
        """
        print("Executando: Teste 1 - Página Inicial (/)")
        
        # Faz um request GET para a URL raiz
        response = self.client.get(reverse('index'))
        
        # Verifica se a resposta foi "OK" (status code 200)
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o template correto foi usado
        self.assertTemplateUsed(response, 'core/index.html')
        self.assertTemplateUsed(response, 'core/base.html')

    # Para testar o histórico, precisamos simular (mockar) a chamada ao MongoDB
    @patch('chat.services.mongo_service.get_all_chats_paginated')
    def test_02_historico_page_loads(self, mock_get_chats):
        """
        Plano de Ação 2: Testa se a página de histórico (/chat/historico/) carrega.
        """
        print("Executando: Teste 2 - Página de Histórico (/chat/historico/)")
        
        # Configura o mock: Simula o retorno da função do MongoDB
        # Retorna uma lista vazia, 0 chats no total, 0 páginas
        mock_get_chats.return_value = ([], 0, 0) 
        
        # Faz um request GET para a URL do histórico
        response = self.client.get(reverse('chat:historico'))
        
        # Verifica se a resposta foi "OK" (status code 200)
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o template correto foi usado
        self.assertTemplateUsed(response, 'chat/historico.html')
        
        # Verifica se a função de mock foi chamada
        mock_get_chats.assert_called_once()

    # Para testar a API, precisamos simular (mockar):
    # 1. A geração da IA (para ser rápido e não carregar o modelo)
    # 2. As chamadas ao MongoDB (para não usar o banco real)
    @patch('chat.services.mongo_service.create_chat', MagicMock(return_value="mock_chat_id_123"))
    @patch('chat.services.mongo_service.add_message', MagicMock(return_value=True))
    @patch('chat.services.mongo_service.get_chat_history', MagicMock(return_value=[{"role": "user", "content": "teste"}]))
    @patch('chat.services.mongo_service.update_last_assistant_message_metadata', MagicMock(return_value=True))
    @patch('chat.services.nlp_service.gerar_resposta_com_contexto', MagicMock(return_value="Esta é uma resposta mockada da IA"))
    def test_03_gerar_resposta_api(self):
        """
        Plano de Ação 3: Simula um "POST" para a API (/chat/gerar/)
        e verifica se recebe um JSON de volta.
        """
        print("Executando: Teste 3 - API POST (/chat/gerar/)")
        
        # Dados que o frontend enviaria
        post_data = {
            'prompt': 'Olá, mundo!',
            'chat_id': '' # Inicia um novo chat
        }
        
        # Faz a requisição POST para a API, enviando dados como JSON
        response = self.client.post(
            reverse('chat:gerar_resposta'),
            data=json.dumps(post_data),
            content_type='application/json'
        )
        
        # 1. Verifica se a resposta foi "OK" (status code 200)
        self.assertEqual(response.status_code, 200)
        
        # 2. Verifica se a resposta é um JSON
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        
        # 3. Verifica o conteúdo da resposta JSON
        data = response.json()
        self.assertIn('chat_id', data)
        self.assertIn('response', data)
        self.assertEqual(data['chat_id'], "mock_chat_id_123") # O valor que definimos no mock
        self.assertEqual(data['response'], "Esta é uma resposta mockada da IA") # O valor do mock da IA
