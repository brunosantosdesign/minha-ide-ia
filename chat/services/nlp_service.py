import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time
from typing import List, Dict
import traceback # Para log detalhado

# --- Carregamento Singleton do Modelo de IA ---
MODEL_NAME = "Qwen/Qwen2-0.5B-Instruct" # Mesmo modelo do main.py original
tokenizer = None
model = None
is_model_loaded = False

try:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando o carregamento do modelo de IA: {MODEL_NAME}...")
    start_load_time = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto", # Usa o tipo de dado recomendado
        device_map="cpu" # Força CPU para consistência
    )
    is_model_loaded = True
    end_load_time = time.time()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Modelo '{MODEL_NAME}' carregado com sucesso em {round(end_load_time - start_load_time, 2)} segundos.")
except Exception as e:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO CRÍTICO: Não foi possível carregar o modelo '{MODEL_NAME}'.")
    traceback.print_exc() # Loga o erro completo

def gerar_resposta_com_contexto(chat_history: List[Dict]) -> str:
    """
    Gera uma resposta usando o modelo carregado, considerando o histórico.
    Adapta a lógica do main.py original.
    """
    if not is_model_loaded or not model or not tokenizer:
        raise Exception("O modelo de IA não foi carregado corretamente.")

    try:
        if not chat_history:
            # Se o histórico estiver vazio (primeira mensagem), retorna um erro ou uma resposta padrão
            # Isto não deve acontecer porque a view sempre adiciona a mensagem do user primeiro
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Aviso: Tentativa de gerar resposta com histórico vazio.")
            return "Desculpe, ocorreu um problema ao processar o histórico."

        # Obtem o último prompt do utilizador para log
        last_user_prompt = chat_history[-1]['content']
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Gerando resposta para: '{last_user_prompt[:50]}...' com {len(chat_history)} mensagens no histórico.")
        start_gen_time = time.time()

        # Prepara a conversa para o modelo, incluindo a instrução de sistema e o histórico
        messages_for_model = [{"role": "system", "content": "Você é um assistente prestativo que responde em português."}]
        # Adiciona o histórico formatado
        for msg in chat_history:
             # Garante que só passa 'role' e 'content'
             messages_for_model.append({"role": msg.get("role"), "content": msg.get("content")})

        # Formata o texto usando o template do modelo Qwen2
        # É crucial usar add_generation_prompt=True para indicar ao modelo que ele deve responder
        text = tokenizer.apply_chat_template(
            messages_for_model,
            tokenize=False,
            add_generation_prompt=True
        )

        # Converte para tensores e move para CPU
        model_inputs = tokenizer([text], return_tensors="pt").to("cpu")

        # Gera os IDs da resposta
        # NOTA: Ajuste max_new_tokens conforme necessário
        generated_ids = model.generate(
            model_inputs.input_ids,
            max_new_tokens=512
        )

        # Ignora os tokens do input original ao descodificar
        # Pega todos os tokens gerados APÓS o final do input
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):]
        response_text = tokenizer.decode(output_ids, skip_special_tokens=True)

        end_gen_time = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Resposta gerada em {round(end_gen_time - start_gen_time, 2)} segundos.")

        # Tratamento de possíveis artefactos no final da resposta (comum em alguns modelos)
        response_text = response_text.replace("<|im_end|>", "").strip()
        # Remove a repetição do prompt inicial se ocorrer (menos comum com apply_chat_template)
        # if response_text.startswith(last_user_prompt):
        #    response_text = response_text[len(last_user_prompt):].strip()


        return response_text

    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Erro durante a geração da resposta com contexto:")
        traceback.print_exc()
        # Retorna uma mensagem de erro que será mostrada ao utilizador
        return f"Desculpe, ocorreu um erro ao gerar a resposta: {e}"

