from pathlib import Path
import json
import pickle
import re
import unicodedata

from rank_bm25 import BM25Okapi


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PASTA_CHUNKS = ROOT / "dados_processados" / "chunks"
PASTA_BM25 = ROOT / "dados_processados" / "bm25"

ARQUIVO_CHUNKS = PASTA_CHUNKS / "chunks.json"

ARQUIVO_INDICE = PASTA_BM25 / "bm25.pkl"
ARQUIVO_DOCUMENTOS = PASTA_BM25 / "documentos_bm25.json"


# ============================================================
# GARANTIR ESTRUTURA
# ============================================================

PASTA_BM25.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# VALIDAR ENTRADA
# ============================================================

if not ARQUIVO_CHUNKS.exists():

    print("[ERRO] chunks.json não encontrado.")

    print("\nExecute primeiro:")
    print("python .\\scripts\\02_criar_chunks.py")

    raise SystemExit(1)


# ============================================================
# TOKENIZAÇÃO
# ============================================================

def remover_acentos(texto: str) -> str:
    """
    Remove acentos para ajudar a busca lexical.

    Exemplo:
    'títulos' -> 'titulos'
    """

    texto_normalizado = unicodedata.normalize(
        "NFD",
        texto
    )

    return "".join(
        caractere
        for caractere in texto_normalizado
        if unicodedata.category(caractere) != "Mn"
    )


def tokenizar(texto: str) -> list[str]:
    """
    Tokenização simples para português.

    - converte para minúsculas
    - remove acentos
    - mantém apenas palavras e números
    """

    texto = texto.lower()

    texto = remover_acentos(texto)

    tokens = re.findall(
        r"\b[a-z0-9]+\b",
        texto
    )

    return tokens


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
print("05 - CRIAÇÃO DO ÍNDICE BM25")
print("=" * 70)

print(f"\nChunks recebidos: {len(chunks)}")


# ============================================================
# PREPARAR CORPUS
# ============================================================

corpus_tokenizado = []

documentos_bm25 = []


for chunk in chunks:

    tokens = tokenizar(
        chunk["texto"]
    )

    corpus_tokenizado.append(
        tokens
    )

    documentos_bm25.append(
        {
            "chunk_id": chunk["chunk_id"],
            "arquivo": chunk["arquivo"],
            "categoria": chunk["categoria"],
            "texto": chunk["texto"],
            "tokens": tokens
        }
    )


# ============================================================
# CRIAR BM25
# ============================================================

print("\nCriando índice BM25...")

bm25 = BM25Okapi(
    corpus_tokenizado
)

print("[OK] Índice BM25 criado.")


# ============================================================
# SALVAR ÍNDICE
# ============================================================

with open(
    ARQUIVO_INDICE,
    "wb"
) as arquivo:

    pickle.dump(
        bm25,
        arquivo
    )


# ============================================================
# SALVAR DOCUMENTOS / METADADOS
# ============================================================

with open(
    ARQUIVO_DOCUMENTOS,
    "w",
    encoding="utf-8"
) as arquivo:

    json.dump(
        documentos_bm25,
        arquivo,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# RESUMO
# ============================================================

print("\n" + "=" * 70)

print(f"Documentos indexados: {len(documentos_bm25)}")

print(f"\nÍndice BM25:")
print(ARQUIVO_INDICE)

print(f"\nMetadados BM25:")
print(ARQUIVO_DOCUMENTOS)

print("=" * 70)


# ============================================================
# TESTE SIMPLES
# ============================================================

PERGUNTA_TESTE = "Quantas Libertadores o Flamengo tem?"

tokens_pergunta = tokenizar(
    PERGUNTA_TESTE
)

scores = bm25.get_scores(
    tokens_pergunta
)


ranking = sorted(
    enumerate(scores),
    key=lambda x: x[1],
    reverse=True
)


print("\nTESTE BM25")
print("-" * 70)

print(f"Pergunta: {PERGUNTA_TESTE}")
print(f"Tokens: {tokens_pergunta}")


print("\nTop 3 resultados:\n")


for posicao, (indice, score) in enumerate(
    ranking[:3],
    start=1
):

    documento = documentos_bm25[indice]

    print(
        f"{posicao}. "
        f"chunk_id={documento['chunk_id']} "
        f"| score={score:.4f}"
    )

    print(
        f"   arquivo={documento['arquivo']}"
    )

    print(
        f"   categoria={documento['categoria']}"
    )

    print(
        f"   texto={documento['texto'][:250]}..."
    )

    print()


print("-" * 70)