import torch
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# ---------------------------
# 1️⃣ Conexão com MongoDB
# ---------------------------
client = MongoClient("mongodb://localhost:27017")
db = client["chatgpt_local"]
chats_collection = db["chats"]

# ---------------------------
# 2️⃣ Funções auxiliares
# ---------------------------
def create_chat(title="Novo Chat"):
    chat = {
        "title": title,
        "created_at": datetime.utcnow(),
        "messages": []
    }
    result = chats_collection.insert_one(chat)
    return str(result.inserted_id)

def add_message(chat_id, role, content):
    chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {"messages": {"role": role, "content": content}}}
    )

def delete_chat(chat_id):
    chats_collection.delete_one({"_id": ObjectId(chat_id)})

def get_chat_history(chat_id):
    chat = chats_collection.find_one({"_id": ObjectId(chat_id)})
    if chat:
        return chat["messages"]
    return []

# ---------------------------
# 3️⃣ Carregamento do modelo
# ---------------------------
MODEL_NAME = "Qwen/Qwen2-0.5B-Instruct"
tokenizer = None
model = None

print("Iniciando carregamento do modelo...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="cpu"
    )
    print(f"Modelo '{MODEL_NAME}' carregado com sucesso!")
except Exception as e:
    print(f"ERRO CRÍTICO: não foi possível carregar o modelo. Erro: {e}")

# ---------------------------
# 4️⃣ Configuração FastAPI
# ---------------------------
app = FastAPI()
class PromptRequest(BaseModel):
    prompt: str

# ---------------------------
# 5️⃣ Endpoint para gerar resposta
# ---------------------------
@app.post("/gerar")
async def gerar_resposta(request: PromptRequest, chat_id: str = None):
    if not model or not tokenizer:
        raise HTTPException(status_code=500, detail="O modelo não está carregado.")

    try:
        # Cria chat se não houver chat_id
        if not chat_id:
            chat_id = create_chat()
            print(f"[DEBUG] Novo chat criado: {chat_id}")
        else:
            print(f"[DEBUG] Usando chat_id existente: {chat_id}")

        # Salva mensagem do usuário
        add_message(chat_id, "user", request.prompt)
        print(f"[DEBUG] Mensagem do usuário adicionada: {request.prompt}")

        # Concatena histórico para entrada do modelo
        messages = get_chat_history(chat_id)
        print(f"[DEBUG] Histórico atual: {messages}")

        text_input = "Sistema: Você é um assistente prestativo que responde em português.\n"
        for msg in messages:
            role = "Usuário" if msg["role"] == "user" else "Assistente"
            text_input += f"{role}: {msg['content']}\n"
        text_input += "Assistente: "

        # Geração da resposta
        model_inputs = tokenizer(text_input, return_tensors="pt").to("cpu")
        generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=512)
        decoded_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        response_text = decoded_output.split("Assistente:")[-1].strip()
        print(f"[DEBUG] Resposta do assistente gerada: {response_text}")

        # Salva a resposta do assistente
        add_message(chat_id, "assistant", response_text)
        print(f"[DEBUG] Resposta do assistente adicionada ao chat {chat_id}")

        # Retorna chat_id + resposta
        return {"chat_id": chat_id, "response": response_text}

    except Exception as e:
        print(f"[ERRO] Durante a geração da resposta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# 6️⃣ Endpoint para consultar histórico
# ---------------------------
@app.get("/chats/{chat_id}")
async def ver_chat(chat_id: str):
    history = get_chat_history(chat_id)
    return {"chat_id": chat_id, "messages": history}

# ---------------------------
# Endpoint para consultar todos os chats
# ---------------------------
@app.get("/chats")
async def ver_todos_chats():
    chats = []
    for chat in chats_collection.find():
        chats.append({
            "chat_id": str(chat["_id"]),
            "title": chat.get("title", "Sem título"),
            "created_at": chat.get("created_at"),
            "messages": chat.get("messages", [])
        })
    return {"chats": chats}


# ---------------------------
# 7️⃣ Endpoint para deletar chat
# ---------------------------
@app.delete("/chats/{chat_id}")
async def apagar_chat(chat_id: str):
    delete_chat(chat_id)
    return {"detail": "Chat deletado com sucesso."}

# ---------------------------
# 8️⃣ Montagem de arquivos estáticos
# ---------------------------
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# ---------------------------
# 9️⃣ Execução do servidor
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
