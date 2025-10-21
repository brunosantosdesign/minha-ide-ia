import torch
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- 1. Configuração da Aplicação FastAPI ---
app = FastAPI()

# --- 2. Carregamento do Modelo de IA ---
# Usaremos um modelo da família Qwen, que é leve e eficiente para rodar em CPU.
MODEL_NAME = "Qwen/Qwen2-0.5B-Instruct"
tokenizer = None
model = None

print("Iniciando o carregamento do modelo...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="cpu"  # Garante que o modelo rode na CPU
    )
    print(f"Modelo '{MODEL_NAME}' carregado com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível carregar o modelo. Erro: {e}")

# --- 3. Definição dos Dados de Entrada da API ---
class PromptRequest(BaseModel):
    prompt: str

# --- 4. Rota da API para Gerar Respostas ---
@app.post("/gerar")
async def gerar_resposta(request: PromptRequest):
    if not model or not tokenizer:
        raise HTTPException(status_code=500, detail="O modelo não está carregado.")

    try:
        # Prepara a conversa para o modelo, incluindo uma instrução de sistema
        messages = [
            {"role": "system", "content": "Você é um assistente prestativo que responde em português."},
            {"role": "user", "content": request.prompt}
        ]
        
        # Formata o texto para o modelo
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Converte o texto em tokens que o modelo entende
        model_inputs = tokenizer([text], return_tensors="pt").to("cpu")

        # Gera a resposta
        generated_ids = model.generate(
            model_inputs.input_ids,
            max_new_tokens=512  # Limita o tamanho da resposta
        )
        
        # Decodifica os tokens de volta para texto
        decoded_output = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Extrai apenas a resposta do assistente
        response_text = decoded_output.split("<|im_start|>assistant\n")[-1]

        return {"response": response_text.strip()}

    except Exception as e:
        print(f"Erro durante a geração da resposta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 5. Montagem dos Ficheiros Estáticos (Frontend) ---
# Isto serve a nossa página `index.html` e os outros ficheiros da pasta `static`
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# --- Ponto de Execução (Opcional, para rodar com 'python main.py') ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
