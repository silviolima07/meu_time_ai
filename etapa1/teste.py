from pathlib import Path
import sys

from faster_whisper import WhisperModel


# ============================================================
# CAMINHOS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
ARQUIVO_AUDIO = Path(__file__).resolve().parent / "audio.ogg"

# Permite importar rag_core.py da pasta scripts
sys.path.insert(
    0,
    str(ROOT / "scripts")
)

from rag_core import (
    busca_hibrida,
    montar_contexto,
    perguntar_llm,
    salvar_log,
)


# ============================================================
# WHISPER
# ============================================================

print("\nCarregando Whisper...")

modelo_whisper = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("[OK] Whisper carregado.")


# ============================================================
# TRANSCREVER
# ============================================================

print("\nTranscrevendo áudio...")

segments, info = modelo_whisper.transcribe(
    str(ARQUIVO_AUDIO),
    language="pt"
)

pergunta = " ".join(
    segment.text.strip()
    for segment in segments
).strip()

print(f"\nIdioma: {info.language}")
print(f"Pergunta transcrita: {pergunta}")


# ============================================================
# RAG
# ============================================================

print("\nExecutando busca híbrida...")

resultados = busca_hibrida(
    pergunta
)

contexto = montar_contexto(
    resultados
)

print("\nConsultando LLM...")

resposta = perguntar_llm(
    pergunta,
    contexto
)

salvar_log(
    pergunta,
    resposta,
    resultados
)


# ============================================================
# RESULTADO
# ============================================================

print("\n" + "=" * 70)
print("RESPOSTA")
print("=" * 70)

print(resposta)
