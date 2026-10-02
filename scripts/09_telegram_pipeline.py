from pathlib import Path
import os
import asyncio

import tempfile
import numpy as np
import soundfile as sf

from faster_whisper import WhisperModel

import subprocess
from io import BytesIO


from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

print("Inicializando RAG, aguarde...")

from rag_core import (
    busca_hibrida,
    montar_contexto,
    perguntar_llm,
    salvar_log,
)

print("[OK] RAG inicializado.")


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(
    ROOT / ".env"
)

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN não definido no arquivo .env."
    )


# ============================================================
# MODELOS DE ÁUDIO
# ============================================================

print("\nCarregando modelo Whisper...")

modelo_whisper = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("[OK] Whisper carregado.")


modelo_tts = None


# ============================================================
# PREFERÊNCIAS
# ============================================================

preferencias_resposta = {}


def obter_modo_resposta(user_id: int) -> str:

    return preferencias_resposta.get(
        user_id,
        "texto"
    )


async def modo_texto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    preferencias_resposta[user_id] = "texto"

    await update.message.reply_text(
        "💬 Modo de resposta alterado para texto."
    )


async def modo_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    preferencias_resposta[user_id] = "audio"

    await update.message.reply_text(
        "🔊 Modo de resposta alterado para áudio."
    )

# Funçoes auxiliares

def transcrever_audio(
    arquivo_audio: str
) -> str:

    segments, _ = modelo_whisper.transcribe(
        arquivo_audio,
        language="pt"
    )

    texto = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return texto.strip()


import re

def limpar_markdown_para_audio(texto: str) -> str:
    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.*?)\*", r"\1", texto)
    texto = re.sub(r"`(.*?)`", r"\1", texto)
    texto = re.sub(r"#+\s*", "", texto)

    return texto.strip()


import re


def limpar_markdown(texto: str) -> str:

    texto = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        texto
    )

    texto = re.sub(
        r"\*(.*?)\*",
        r"\1",
        texto
    )

    texto = re.sub(
        r"`(.*?)`",
        r"\1",
        texto
    )

    texto = re.sub(
        r"^#+\s*",
        "",
        texto,
        flags=re.MULTILINE
    )

    return texto.strip()

# Piper

PIPER_MODEL = (
    Path(__file__).resolve().parent.parent
    / "modelos"
    / "piper"
    / "pt_BR-faber-medium"
    / "pt_BR-faber-medium.onnx"
)

def gerar_audio(texto: str, arquivo_saida: str):
    subprocess.run(
        [
            "piper",
            "--model",
            str(PIPER_MODEL),
            "--output_file",
            arquivo_saida,
        ],
        input=texto,
        text=True,
        check=True,
    )


# Função enviar a resposta

async def enviar_resposta(
    update: Update,
    resposta: str
):

    user_id = update.effective_user.id

    modo = obter_modo_resposta(
        user_id
    )
    
    print(f"[DEBUG] Modo de Resposta: {modo}")

    resposta_limpa = limpar_markdown(
        resposta
    )

    if modo == "texto":
        print("[DEBUG]	 Enviando resposta em texto")
        await update.message.reply_text(
            "⚽ Meu Time IA\n\n"
            f"{resposta_limpa}"
        )

        return
    
    print(f"[DEBUG] Entrando na geração de aúdio.")

    with tempfile.TemporaryDirectory() as pasta:

        arquivo_audio = Path(pasta) / "resposta.wav"

        print(f"[DEBUG] Gerando arquivo: {arquivo_audio}")

        arquivo_wav = Path(pasta) / "resposta.wav"
        arquivo_ogg = Path(pasta) / "resposta.ogg"
        

        t0 = time.perf_counter()

        await asyncio.to_thread(
            gerar_audio,
            resposta_limpa,
            str(arquivo_wav)
        )
        
        print(f"[TEMPO] Piper/TTS: "
              f"{time.perf_counter() - t0:.2f}s"
              )
   
        print("[DEBUG]  Áudio gerado")
        
        t0 = time.perf_counter()
    
        subprocess.run(
        [
        "ffmpeg",
        "-y",
        "-i",
        str(arquivo_wav),
        "-c:a",
        "libopus",
        str(arquivo_ogg)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
        ) 
        
        print(f"[TEMPO] FFmpeg: "
              f"{time.perf_counter() - t0:.2f}s"
              )

        with open(arquivo_ogg, "rb") as f:
            dados_audio = f.read()

        audio = BytesIO(dados_audio)
        audio.name = "resposta.ogg"
        
        print("[DEBUG] Enviando Áudio para Telegram")
        
        t0 = time.perf_counter()
        
        await update.message.reply_voice(
            voice=audio
        )

        print(f"[TEMPO] Envio Telegram: "
              f"{time.perf_counter() - t0:.2f}s"
              )

        print("[OK] Mensagem de voz enviada.") 

        print("[DEBUG] Áudio enviado")
 


# Audio vindo do Telegram

async def receber_audio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.voice:
        return

    await update.message.reply_text(
        "🎙️ Áudio recebido. Transcrevendo..."
    )

    try:

        arquivo_telegram = (
            await context.bot.get_file(
                update.message.voice.file_id
            )
        )

        with tempfile.TemporaryDirectory() as pasta:

            arquivo_audio = (
                Path(pasta)
                / "pergunta.ogg"
            )

            await arquivo_telegram.download_to_drive(
                custom_path=str(arquivo_audio)
            )

            pergunta = await asyncio.to_thread(
                transcrever_audio,
                str(arquivo_audio)
            )

            print(
                f"\nPergunta transcrita: {pergunta}"
            )

            await update.message.reply_text(
                "📝 Entendi:\n"
                f"{pergunta}"
            )

            modo = obter_modo_resposta(update.effective_user.id)

            resposta = await asyncio.to_thread(
                processar_pergunta,
                pergunta,
                modo
            )

            await enviar_resposta(
                update,
                resposta
            )

    except Exception as erro:

        print(
            f"\n[ERRO ÁUDIO] {erro}"
        )

        await update.message.reply_text(
            "Não consegui processar o áudio."
        )




# ============================================================
# PROCESSAR PERGUNTA
# ============================================================
import  time

def processar_pergunta(pergunta: str, modo_resposta: str = "texto") -> str:
    
    inicio_total= time.perf_counter()
    t0 = time.perf_counter()

    print(
        f"\nPergunta recebida:"
        f"\n{pergunta}"
    )

    # Retrieval
    resultados = busca_hibrida(
        pergunta
    )

    # Contexto
    contexto = montar_contexto(
        resultados
    )

    print(f"[TEMPO] Contexto: "
          f"{time.perf_counter() - t0:.2f}s"
          )

    t0 = time.perf_counter()

    # LLM
    resposta = perguntar_llm(
        pergunta,
        contexto,
        modo_resposta
    )
    print( f"[TEMPO] LLM: "
           f"{time.perf_counter() - t0:.2f}s"
          )
    t0 = time.perf_counter()


    # Auditoria
    salvar_log(
        pergunta,
        resposta,
        resultados
    )
    print(f"[TEMPO] Log: "
          f"{time.perf_counter() - t0:.2f}s"

           )
    print(f"[TEMPO] Total: "
           f"{time.perf_counter() - inicio_total:.2f}s"
          )
    return resposta


# ============================================================
# COMANDO /start


# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "⚽ Meu Time IA\n\n"
        "Você pode fazer perguntas por texto ou áudio.\n\n"
        "💬 /texto - receber respostas em texto\n"
        "🔊 /audio - receber respostas em áudio\n\n"
        "O modo padrão é texto."
    )

# ============================================================
# RECEBER MENSAGENS
# ============================================================

async def receber_mensagem(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    pergunta = update.message.text

    if not pergunta:
        return

    usuario = update.effective_user

    print(
        "\n" + "-" * 70
    )

    print(
        f"Usuário: "
        f"{usuario.id if usuario else 'desconhecido'}"
    )

    print(
        f"Pergunta: {pergunta}"
    )

    try:

        # Executa o RAG em outra thread para não bloquear
        # o loop assíncrono do Telegram.

        modo = obter_modo_resposta(update.effective_user.id)

        resposta = await asyncio.to_thread(
            processar_pergunta,
            pergunta,
            modo
        )

        await enviar_resposta(
            update,
            resposta
        )

        print(
            "\n[OK] Resposta enviada."
        )

    except Exception as erro:

        print(
            f"\n[ERRO] {erro}"
        )

        await update.message.reply_text(
            "Ocorreu um erro ao processar sua pergunta."
        )
# ============================================================
# ERROS
# ============================================================

async def tratar_erro(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        f"\n[ERRO TELEGRAM] "
        f"{context.error}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "MEU TIME IA - TELEGRAM"
    )

    print(
        "=" * 70
    )

    print(
        "\nAguardando mensagens..."
    )

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "texto",
            modo_texto
        )
    )
    
    application.add_handler(
        CommandHandler(
            "audio",
            modo_audio
        )
    )

    application.add_handler(
        MessageHandler(
            filters.VOICE,
            receber_audio
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receber_mensagem
        )
    )

    application.add_error_handler(
        tratar_erro
    )

    application.run_polling()


if __name__ == "__main__":

    main()

