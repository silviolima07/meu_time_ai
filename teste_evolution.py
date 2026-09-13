import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("EVO_BASE_URL")
API_KEY = os.getenv("AUTHENTICATION_API_KEY")
INSTANCE = os.getenv("EVO_INSTANCE_NAME")

#print("EVO_BASE_URL =", os.getenv("EVO_BASE_URL"))
#print("EVOLUTION_API_URL =", os.getenv("EVOLUTION_API_URL"))
#print("INSTANCE =", os.getenv("EVO_INSTANCE_NAME"))

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json",
}

# 1. Buscar mensagens
url = f"{BASE_URL}/chat/findMessages/{INSTANCE}"

response = requests.post(
    url,
    headers=headers,
    json={"where": {}},
    timeout=20,
)

response.raise_for_status()

dados = response.json()

records = dados["messages"]["records"]

# Procurar a mensagem recebida mais recente
recebidas = [
    msg for msg in records
    if not msg.get("key", {}).get("fromMe", False)
]

if not recebidas:
    print("Nenhuma mensagem recebida encontrada.")
    raise SystemExit

ultima = recebidas[0]

key = ultima["key"]

# Evolution pode usar LID como remoteJid.
# O número real aparece em remoteJidAlt quando disponível.
remote_jid = key.get("remoteJidAlt") or key.get("remoteJid")

numero = remote_jid.split("@")[0]

mensagem = ultima.get("message", {}).get("conversation")

print("Número:", numero)
print("Mensagem recebida:", mensagem)

# 2. Responder
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "openai/gpt-oss-120b", # "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é o Meu Time IA, um assistente de futebol. "
                    "Responda de forma clara, curta e em português."
                ),
            },
            {
                "role": "user",
                "content": mensagem,
            },
        ],
        "temperature": 0.7,
    },
    timeout=30,
)

groq_response.raise_for_status()

resposta = groq_response.json()["choices"][0]["message"]["content"]

print("Resposta da IA:", resposta)

url_envio = f"{BASE_URL}/message/sendText/{INSTANCE}"

r = requests.post(
    url_envio,
    headers=headers,
    json={
        "number": numero,
        "text": resposta,
    },
    timeout=20,
)

r.raise_for_status()

print("Resposta enviada!")
print(r.json())