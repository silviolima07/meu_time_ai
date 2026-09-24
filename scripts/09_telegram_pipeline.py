from pathlib import Path
import os
import asyncio

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from rag_core import (
    busca_hibrida,
    montar_contexto,
    perguntar_llm,
    salvar_log,
)


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
# PROCESSAR PERGUNTA
# ============================================================

def processar_pergunta(pergunta: str) -> str:

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

    # LLM
    resposta = perguntar_llm(
        pergunta,
        contexto
    )

    # Auditoria
    salvar_log(
        pergunta,
        resposta,
        resultados
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
        "Olá! Pergunte algo sobre o seu time."
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
        resposta = await asyncio.to_thread(
            processar_pergunta,
            pergunta
        )

        resposta_telegram = (
            "⚽ Meu Time IA\n\n"
            f"{resposta}"
        )

        await update.message.reply_text(
            resposta_telegram,
            parse_mode="Markdown"
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

