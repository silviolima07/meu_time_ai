from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import sys
import hmac

BASE_DIR = Path(__file__).resolve().parent

# Carrega a chave local sem precisar instalar dependências
env_path = BASE_DIR / ".env.api"

if env_path.exists():
    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        if chave.strip() == "BACKEND_API_KEY":
            os.environ.setdefault(
                "BACKEND_API_KEY", valor.strip().strip('"').strip("'")
            )

API_KEY = os.environ.get("BACKEND_API_KEY", "")

if not API_KEY:
    raise RuntimeError("BACKEND_API_KEY não configurada")

sys.path.insert(0, str(BASE_DIR / "scripts"))

from rag_core import busca_hibrida, montar_contexto, perguntar_llm
from audio_service import gerar_audio_ogg


class Handler(BaseHTTPRequestHandler):

    def responder_json(self, status, conteudo):
        dados = json.dumps(conteudo, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.path != "/health":
            self.responder_json(404, {"erro": "Endpoint não encontrado"})
            return

        self.responder_json(200, {
            "status": "online",
            "servico": "Meu Time IA - Homologacao"
        })

    def do_POST(self):
        if self.path not in ("/perguntar", "/perguntar/audio"):
            self.responder_json(404, {"erro": "Endpoint não encontrado"})
            return

        chave_recebida = self.headers.get("X-Backend-API-Key", "")

        if not hmac.compare_digest(chave_recebida, API_KEY):
            self.responder_json(401, {"erro": "Não autorizado"})
            return

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))

            if tamanho <= 0 or tamanho > 8192:
                self.responder_json(400, {"erro": "Tamanho inválido"})
                return

            dados = json.loads(self.rfile.read(tamanho))

            if not isinstance(dados, dict):
                self.responder_json(400, {"erro": "JSON inválido"})
                return

            pergunta = dados.get("pergunta", "")
            modo = dados.get("modo", "texto")

            if not isinstance(pergunta, str) or not pergunta.strip():
                self.responder_json(400, {"erro": "Pergunta inválida"})
                return

            if len(pergunta) > 2000:
                self.responder_json(400, {"erro": "Pergunta muito longa"})
                return

            if modo not in ("texto", "audio"):
                self.responder_json(400, {"erro": "Modo inválido"})
                return

            if self.path == "/perguntar/audio":
                modo = "audio"

            resultados = busca_hibrida(pergunta.strip())
            contexto = montar_contexto(resultados)

            resposta = perguntar_llm(
                pergunta.strip(),
                contexto,
                modo
            )

            if self.path == "/perguntar/audio":
                audio = gerar_audio_ogg(resposta)

                self.send_response(200)
                self.send_header("Content-Type", "audio/ogg")
                self.send_header("Content-Length", str(len(audio)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(audio)
                return

            self.responder_json(200, {
                "resposta": resposta,
                "fontes_recuperadas": len(resultados)
            })

        except (ValueError, UnicodeDecodeError):
            self.responder_json(400, {"erro": "JSON inválido"})

        except Exception as erro:
            print(f"Erro no processamento RAG: {erro}", flush=True)
            self.responder_json(500, {
                "erro": "Erro interno ao processar pergunta"
            })


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", 8001), Handler)
    print("API de homologacao iniciada na porta 8001", flush=True)
    servidor.serve_forever()
