from pymongo import MongoClient, errors as MongoErrors
from bson import ObjectId
from datetime import datetime, timezone, time
from django.conf import settings
import traceback
from typing import Dict, List, Optional
import re

# --- Configuração da Conexão Singleton com MongoDB ---
client = None
db = None
chats_collection = None

def _connect_db():
    global client, db, chats_collection
    if db is None:
        try:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Conectando ao MongoDB em {settings.MONGO_URI}...")
            client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                uuidRepresentation='standard'
            )
            client.admin.command('ping')
            db = client[settings.MONGO_DB_NAME]
            chats_collection = db["chats"]
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Conectado com sucesso ao MongoDB, base de dados: '{settings.MONGO_DB_NAME}'")
        except Exception as e:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] ERRO CRÍTICO: Não foi possível conectar ao MongoDB. Erro: {e}")
            db = None
            chats_collection = None

def get_chats_collection():
    if chats_collection is None:
        _connect_db()
    return chats_collection

# --- Funções CRUD (create_chat, add_message, etc.) ---
# ... (O restante das funções CRUD: create_chat, add_message, get_chat_history, update_last_assistant_message_metadata ... permanecem iguais) ...
def create_chat(title="Novo Chat") -> str | None:
    collection = get_chats_collection()
    if collection is None:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Não foi possível obter a coleção 'chats' para criar um novo chat.")
        return None
    model_name = "desconhecido"
    try:
        from . import nlp_service
        model_name = nlp_service.MODEL_NAME if nlp_service.is_model_loaded else "modelo_nao_carregado"
    except Exception as e:
         print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Erro ao obter nome do modelo do nlp_service: {e}")
    chat_document = {
        "title": title,
        "created_at": datetime.now(timezone.utc),
        "messages": [],
        "model_name": model_name
    }
    try:
        result = collection.insert_one(chat_document)
        new_id = str(result.inserted_id)
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Novo chat criado com ID: {new_id}")
        return new_id
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao criar chat no MongoDB:")
        traceback.print_exc()
        return None

def add_message(chat_id: str, role: str, content: str):
    collection = get_chats_collection()
    if collection is None:
         print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Coleção 'chats' não disponível para adicionar mensagem ao chat {chat_id}.")
         return False
    if role not in ['user', 'assistant']:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Role inválido '{role}' ao adicionar mensagem ao chat {chat_id}.")
        return False
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc)
    }
    try:
        if not ObjectId.is_valid(chat_id):
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: ID do chat inválido '{chat_id}' ao adicionar mensagem.")
             return False
        result = collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"messages": message}}
        )
        if result.matched_count == 0:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Chat com ID {chat_id} não encontrado para adicionar mensagem.")
            return False
        else:
            return True
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao adicionar mensagem ao chat {chat_id}:")
        traceback.print_exc()
        return False

def get_chat_history(chat_id: str) -> Optional[List[Dict]]:
    collection = get_chats_collection()
    if collection is None:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Coleção 'chats' não disponível para obter histórico do chat {chat_id}.")
        return None
    try:
        if not ObjectId.is_valid(chat_id):
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: ID do chat inválido '{chat_id}' ao obter histórico.")
             return None
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        if chat:
            return chat.get("messages", [])
        else:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Chat com ID {chat_id} não encontrado ao obter histórico.")
            return []
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao obter histórico do chat {chat_id}:")
        traceback.print_exc()
        return None

def update_last_assistant_message_metadata(chat_id: str, metadata: dict):
    collection = get_chats_collection()
    if collection is None:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Coleção 'chats' não disponível para atualizar metadados no chat {chat_id}.")
        return False
    try:
        if not ObjectId.is_valid(chat_id):
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: ID do chat inválido '{chat_id}' ao atualizar metadados.")
             return False
        chat_document = collection.find_one({"_id": ObjectId(chat_id)})
        if not chat_document:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Chat {chat_id} não encontrado para atualizar metadados.")
            return False
        messages = chat_document.get("messages", [])
        last_assistant_index = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                last_assistant_index = i
                break
        if last_assistant_index != -1:
            for key, value in metadata.items():
                if isinstance(chat_document["messages"][last_assistant_index], dict):
                     chat_document["messages"][last_assistant_index][key] = value
                else:
                     print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Mensagem no índice {last_assistant_index} do chat {chat_id} não é um dicionário.")
                     return False
            result = collection.replace_one({"_id": ObjectId(chat_id)}, chat_document)
            if result.modified_count > 0:
                return True
            else:
                print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Nenhuma modificação feita nos metadados do chat {chat_id}.")
                return False
        else:
            print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Nenhuma mensagem 'assistant' encontrada no chat {chat_id} para atualizar metadados.")
            return False
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao atualizar metadados 'assistant' no chat {chat_id}:")
        traceback.print_exc()
        return False

# --- Lógica de Filtro (Função Auxiliar) ---

def _build_mongo_query(filters: Optional[dict] = None) -> dict:
    """ Constrói a query do MongoDB a partir dos filtros. """
    query = {}
    if not filters:
        return query

    if filters.get('search_query'):
        search_regex = re.compile(re.escape(filters['search_query']), re.IGNORECASE)
        query['$or'] = [
            {'title': search_regex},
            {'messages.content': search_regex}
        ]
    
    date_query = {}
    try:
        if filters.get('date_from'):
            date_from_obj = datetime.strptime(filters['date_from'], '%Y-%m-%d')
            date_query['$gte'] = datetime.combine(date_from_obj.date(), time.min, tzinfo=timezone.utc)
        
        if filters.get('date_to'):
            date_to_obj = datetime.strptime(filters['date_to'], '%Y-%m-%d')
            date_query['$lte'] = datetime.combine(date_to_obj.date(), time.max, tzinfo=timezone.utc)
    
    except ValueError:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: Formato de data inválido nos filtros.")
        date_query = {}

    if date_query:
        query['created_at'] = date_query
        
    return query

# --- Funções de Busca (Atualizada e Nova) ---

def get_all_chats_paginated(page: int = 1, per_page: int = 10, filters: Optional[dict] = None):
    """ Obtém todos os chats com paginação e filtros. """
    collection = get_chats_collection()
    if collection is None: 
        return [], 0, 0 # Lista, total, páginas

    if page < 1: page = 1
    if per_page < 1: per_page = 10

    skip = (page - 1) * per_page
    query = _build_mongo_query(filters) # Usa a função auxiliar de filtro

    try:
        total_chats = collection.count_documents(query)
        total_pages = (total_chats + per_page - 1) // per_page if per_page > 0 else 0

        chats_cursor = collection.find(
            query,
            {"_id": 1, "title": 1, "created_at": 1, "model_name": 1, "messages": {"$slice": -1}}
        ).sort("created_at", -1).skip(skip).limit(per_page)

        chats_list = []
        for chat in chats_cursor:
             last_message = chat.get("messages", [{}])[0]
             chats_list.append({
                "chat_id": str(chat["_id"]),
                "title": chat.get("title", "Sem título"),
                "created_at": chat.get("created_at"),
                "model_name": chat.get("model_name", "desconhecido"),
                "last_message_preview": last_message.get("content", "")[:50] + "..." if last_message.get("content") else "[Chat vazio]",
                "last_message_time": last_message.get("timestamp")
            })
        return chats_list, total_chats, total_pages
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao buscar chats paginados:")
        traceback.print_exc()
        return [], 0, 0

# --- NOVA FUNÇÃO PARA EXPORTAÇÃO ---
def get_all_chats_for_export(filters: Optional[dict] = None) -> List[Dict]:
    """ Obtém TODOS os chats (sem paginação) para exportação, aplicando filtros. """
    collection = get_chats_collection()
    if collection is None: 
        return []

    query = _build_mongo_query(filters) # Reutiliza a lógica de filtro

    try:
        # Busca todos os documentos que correspondem ao filtro, ordenados
        chats_cursor = collection.find(query).sort("created_at", -1)
        
        chats_list = []
        for chat in chats_cursor:
            # Converte ObjectId para string para serialização
            chat['_id'] = str(chat['_id'])
            # Converte datetimes para strings (bom para JSON)
            if 'created_at' in chat and isinstance(chat['created_at'], datetime):
                chat['created_at'] = chat['created_at'].isoformat()
            if 'messages' in chat:
                for msg in chat['messages']:
                    if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
                        msg['timestamp'] = msg['timestamp'].isoformat()
            chats_list.append(chat)
            
        return chats_list
        
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao buscar todos os chats para exportação:")
        traceback.print_exc()
        return []

# ... (funções get_chat_details e delete_chat permanecem iguais) ...
def get_chat_details(chat_id: str) -> Optional[dict]:
    collection = get_chats_collection()
    if collection is None: return None
    try:
        if not ObjectId.is_valid(chat_id):
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: ID do chat inválido '{chat_id}' ao buscar detalhes.")
             return None
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        if chat:
            chat['_id'] = str(chat['_id'])
            if 'created_at' in chat and isinstance(chat['created_at'], datetime):
                chat['created_at'] = chat['created_at'].isoformat() + 'Z'
            if 'messages' in chat:
                for msg in chat['messages']:
                    if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
                        msg['timestamp'] = msg['timestamp'].isoformat() + 'Z'
            return chat
        else:
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Chat {chat_id} não encontrado ao buscar detalhes.")
             return None
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao buscar detalhes do chat {chat_id}:")
        traceback.print_exc()
        return None

def delete_chat(chat_id: str) -> bool:
    collection = get_chats_collection()
    if collection is None: return False
    try:
        if not ObjectId.is_valid(chat_id):
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro: ID do chat inválido '{chat_id}' para deleção.")
             return False
        result = collection.delete_one({"_id": ObjectId(chat_id)})
        if result.deleted_count > 0:
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Chat {chat_id} deletado com sucesso.")
             return True
        else:
             print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Aviso: Chat {chat_id} não encontrado para deleção.")
             return False
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Erro ao deletar chat {chat_id}:")
        traceback.print_exc()
        return False

