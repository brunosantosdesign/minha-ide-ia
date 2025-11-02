import json
import time
import traceback
import csv # Importa a biblioteca CSV do Python
import io # Importa a biblioteca IO para lidar com streams de texto

from django.http import JsonResponse, HttpRequest, Http404, HttpResponse # Importa HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from django.shortcuts import render
from .services import nlp_service, mongo_service
from django.core.paginator import Paginator
from datetime import datetime # Importa datetime

# --- View da API do Chat (permanece igual) ---
@csrf_exempt
@require_http_methods(["POST"])
def gerar_resposta_view(request: HttpRequest):
    # ... (Esta view permanece igual à da etapa anterior) ...
    try:
        start_time = time.time()
        data = json.loads(request.body)
        prompt = data.get('prompt')
        chat_id = data.get('chat_id')
        if not prompt:
            return JsonResponse({'error': 'O prompt não pode estar vazio.'}, status=400)
        if not chat_id:
            chat_id = mongo_service.create_chat(title=f"Chat: {prompt[:30]}...")
            if not chat_id:
                 print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO CRÍTICO: Não foi possível criar chat no MongoDB.")
                 return JsonResponse({'error': 'Não foi possível criar um novo chat no MongoDB.'}, status=500)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Novo chat ID criado: {chat_id}")
        mongo_service.add_message(chat_id, 'user', prompt)
        history = mongo_service.get_chat_history(chat_id)
        if history is None:
             print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO: Não foi possível obter histórico para o chat {chat_id}.")
             return JsonResponse({'error': f'Não foi possível obter o histórico do chat {chat_id}.'}, status=500)
        response_text = nlp_service.gerar_resposta_com_contexto(history)
        mongo_service.add_message(chat_id, 'assistant', response_text)
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tempo total de processamento da requisição: {processing_time}s")
        mongo_service.update_last_assistant_message_metadata(chat_id, {'processing_time': processing_time, 'model_used': nlp_service.MODEL_NAME})
        return JsonResponse({'chat_id': chat_id, 'response': response_text})
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO na view gerar_resposta_view:")
        traceback.print_exc()
        return JsonResponse({'error': f'Ocorreu um erro interno ao processar o pedido.'}, status=500)

# --- View de Histórico (permanece igual) ---
@require_GET
def historico_view(request: HttpRequest):
    # ... (Esta view permanece igual à da etapa anterior, com filtros e paginação) ...
    try:
        search_query = request.GET.get('query', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        filters = {}
        if search_query:
            filters['search_query'] = search_query
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        page_num = request.GET.get('page', 1)
        try:
            page_num = int(page_num)
        except ValueError:
            page_num = 1
        if page_num < 1:
            page_num = 1
        per_page = 10
        chats_list, total_chats, total_pages = mongo_service.get_all_chats_paginated(
            page=page_num,
            per_page=per_page,
            filters=filters
        )
        paginator = Paginator(range(total_chats), per_page)
        page_obj = paginator.get_page(page_num)
        filter_params = request.GET.copy()
        if 'page' in filter_params:
            del filter_params['page']
        context = {
            'chats': chats_list,
            'page_obj': page_obj,
            'total_pages': total_pages,
            'current_page': page_num,
            'current_query': search_query,
            'current_date_from': date_from,
            'current_date_to': date_to,
            'filter_params': filter_params.urlencode(),
        }
        return render(request, 'chat/historico.html', context)
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO na view historico_view:")
        traceback.print_exc()
        return render(request, 'chat/historico.html', {'error': str(e)})

# --- View de Detalhe do Chat (permanece igual) ---
@require_GET
def chat_detail_view(request: HttpRequest, chat_id: str):
    # ... (Esta view permanece igual à da etapa anterior) ...
    try:
        chat = mongo_service.get_chat_details(chat_id)
        if chat is None:
            raise Http404("Chat não encontrado.")
        context = {
            'chat': chat
        }
        return render(request, 'chat/chat_detalhe.html', context)
    except Http404:
         context = {'error': f"O Chat com ID '{chat_id}' não foi encontrado."}
         return render(request, 'chat/historico.html', context, status=404)
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO na view chat_detail_view:")
        traceback.print_exc()
        return render(request, 'chat/chat_detalhe.html', {'error': str(e)}, status=500)


# --- NOVA VIEW DE EXPORTAÇÃO ---

@require_GET
def exportar_historico_view(request: HttpRequest, format_type: str):
    """
    Exporta o histórico de chats (filtrado) em formato JSON ou CSV.
    """
    try:
        # 1. Reutiliza a lógica de filtro da view de histórico
        search_query = request.GET.get('query', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        filters = {}
        if search_query:
            filters['search_query'] = search_query
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
            
        # 2. Busca TODOS os chats (sem paginação) que correspondem aos filtros
        chats = mongo_service.get_all_chats_for_export(filters=filters)
        
        # Define o nome do arquivo
        filename = f"historico_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 3. Processa o formato solicitado
        if format_type == 'json':
            # Converte os dados (que já são dicts) para uma string JSON
            json_data = json.dumps(chats, indent=2, ensure_ascii=False)
            
            # Cria a resposta HTTP como um arquivo JSON
            response = HttpResponse(json_data, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
            return response

        elif format_type == 'csv':
            # Cria uma resposta HTTP do tipo CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            
            # Garante que o CSV seja escrito corretamente com caracteres UTF-8
            response.write(u'\ufeff'.encode('utf8')) # Adiciona BOM para o Excel entender UTF-8
            
            # Cria um "escritor" de CSV que escreve na resposta HTTP
            writer = csv.writer(response, delimiter=';') # Usa ponto e vírgula, comum no Brasil/Excel
            
            # Escreve o cabeçalho (Header) do CSV
            # Como as mensagens são aninhadas, "achatamos" os dados
            writer.writerow([
                'Chat_ID', 
                'Chat_Titulo', 
                'Chat_Criado_Em', 
                'Modelo',
                'Mensagem_Role', 
                'Mensagem_Conteudo', 
                'Mensagem_Timestamp', 
                'Msg_Tempo_Processamento_Sec'
            ])
            
            # Escreve os dados
            for chat in chats:
                chat_id = chat.get('_id', '')
                chat_title = chat.get('title', '')
                chat_created_at = chat.get('created_at', '')
                model_name = chat.get('model_name', '')
                
                # Se não houver mensagens, escreve uma linha para o chat
                if not chat.get('messages'):
                    writer.writerow([
                        chat_id, chat_title, chat_created_at, model_name,
                        '', '', '', '' # Células vazias para a mensagem
                    ])
                else:
                    # Itera sobre cada mensagem dentro do chat
                    for message in chat.get('messages', []):
                        writer.writerow([
                            chat_id,
                            chat_title,
                            chat_created_at,
                            model_name,
                            message.get('role', ''),
                            message.get('content', ''),
                            message.get('timestamp', ''),
                            message.get('processing_time', '') # Pega o tempo de processamento
                        ])
            return response

        else:
            return JsonResponse({'error': 'Formato de exportação não suportado.'}, status=400)

    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO na view exportar_historico_view:")
        traceback.print_exc()
        # Retorna um erro (poderia ser uma página HTML de erro também)
        return HttpResponse(f"Ocorreu um erro ao exportar os dados: {e}", status=500)

