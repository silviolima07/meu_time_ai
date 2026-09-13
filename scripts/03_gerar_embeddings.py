from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PASTA_PROCESSADOS = ROOT / "dados_processados"
PASTA_CHUNKS = PASTA_PROCESSADOS / "chunks"
PASTA_EMBEDDINGS = PASTA_PROCESSADOS / "embeddings"

ARQUIVO_CHUNKS = PASTA_CHUNKS / "chunks.json"

ARQUIVO_EMBEDDINGS = PASTA_EMBEDDINGS / "embeddings.npy"
ARQUIVO_METADATA = PASTA_EMBEDDINGS / "metadata.json"


# Modelo multilíngue adequado para perguntas em português
MODELO_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


# ============================================================
# GARANTIR ESTRUTURA
# ============================================================

PASTA_EMBEDDINGS.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# VALIDAR ENTRADA
# ============================================================

if not ARQUIVO_CHUNKS.exists():

    print("[ERRO] chunks.json não encontrado.")
    print(f"\nEsperado em:")
    print(ARQUIVO_CHUNKS)

    print("\nExecute primeiro:")
    print("python .\\scripts\\02_criar_chunks.py")

    raise SystemExit(1)


# ============================================================
# CARREGAR CHUNKS
# ============================================================

with open(
    ARQUIVO_CHUNKS,
    "r",
    encoding="utf-8"
) as arquivo:

    chunks = json.load(arquivo)


if not chunks:

    print("[ERRO] Nenhum chunk encontrado.")

    raise SystemExit(1)


print("=" * 70)
print("03 - GERAÇÃO DE EMBEDDINGS")
print("=" * 70)

print(f"\nChunks recebidos: {len(chunks)}")
print(f"Modelo: {MODELO_EMBEDDING}")


# ============================================================
# CARREGAR MODELO
# ============================================================

print("\nCarregando modelo de embeddings...")

modelo = SentenceTransformer(
    MODELO_EMBEDDING
)

print("[OK] Modelo carregado.")


# ============================================================
# PREPARAR TEXTOS
# ============================================================

textos = [
    chunk["texto"]
    for chunk in chunks
]


# ============================================================
# GERAR EMBEDDINGS
# ============================================================

print("\nGerando embeddings...")

embeddings = modelo.encode(
    textos,
    batch_size=16,
    show_progress_bar=True,
    normalize_embeddings=True
)

embeddings = np.asarray(
    embeddings,
    dtype=np.float32
)


# ============================================================
# VALIDAÇÃO
# ============================================================

if len(embeddings) != len(chunks):

    raise RuntimeError(
        "Quantidade de embeddings diferente "
        "da quantidade de chunks."
    )


# ============================================================
# SALVAR EMBEDDINGS
# ============================================================

np.save(
    ARQUIVO_EMBEDDINGS,
    embeddings
)


# ============================================================
# SALVAR METADADOS
# ============================================================

metadata = []

for chunk in chunks:

    metadata.append(
        {
            "chunk_id": chunk["chunk_id"],
            "chunk_documento": chunk["chunk_documento"],
            "time": chunk["time"],
            "arquivo": chunk["arquivo"],
            "categoria": chunk["categoria"],
            "texto": chunk["texto"],
            "tamanho_caracteres": chunk["tamanho_caracteres"]
        }
    )


with open(
    ARQUIVO_METADATA,
    "w",
    encoding="utf-8"
) as arquivo:

    json.dump(
        metadata,
        arquivo,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# RESUMO
# ============================================================

print("\n" + "=" * 70)

print(f"Embeddings gerados: {embeddings.shape[0]}")

print(
    f"Dimensão de cada embedding: "
    f"{embeddings.shape[1]}"
)

print(f"\nArquivo de embeddings:")
print(ARQUIVO_EMBEDDINGS)

print(f"\nArquivo de metadados:")
print(ARQUIVO_METADATA)

print("=" * 70)


# ============================================================
# EXEMPLO
# ============================================================

print("\nEXEMPLO")
print("-" * 70)

print(f"Chunk ID: {metadata[0]['chunk_id']}")
print(f"Arquivo: {metadata[0]['arquivo']}")
print(f"Categoria: {metadata[0]['categoria']}")

print(
    f"Dimensão do vetor: "
    f"{len(embeddings[0])}"
)

print("\nPrimeiros 10 valores do embedding:")

print(
    embeddings[0][:10]
)

print("-" * 70)