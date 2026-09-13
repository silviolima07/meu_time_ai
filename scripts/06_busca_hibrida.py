from pathlib import Path
import json
import pickle
import re
import unicodedata

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PASTA_PROCESSADOS = ROOT / "dados_processados"

PASTA_BM25 = PASTA_PROCESSADOS / "bm25"
PASTA_CHROMA = ROOT / "chroma_db"

ARQUIVO_BM25 = PASTA_BM25 / "bm25.pkl"
ARQUIVO_DOCUMENTOS_BM25 = PASTA_BM25 / "documentos_bm25.json"

NOME_COLECAO = "flamengo"

MODELO_EMBEDDING = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

TOP_K_BM25 = 5
TOP_K_VECTOR = 5
TOP_K_FINAL = 3

RRF_K = 60


# ============================================================
# VALIDAÇÕES
# ============================================================

if not ARQUIVO_BM25.exists():
    print("[ERRO] Índice BM25 não encontrado.")
    print("Execute primeiro:")
    print("python .\\scripts\\05_criar_indice_bm25.py")
    raise SystemExit(1)


if not ARQUIVO_DOCUMENTOS_BM25.exists():
    print("[ERRO] documentos_bm25.json não encontrado.")
    raise SystemExit(1)


if not PASTA_CHROMA.exists():
    print("[ERRO] Banco ChromaDB não encontrado.")
    print("Execute primeiro:")
    print("python .\\scripts\\04_salvar_chroma.py")
    raise SystemExit(1)


# ============================================================
# TOKENIZAÇÃO BM25
# ============================================================

def remover_acentos(texto: str) -> str:

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

    texto = texto.lower()

    texto = remover_acentos(texto)

    return re.findall(
        r"\b[a-z0-9]+\b",
        texto
    )


# ============================================================
# CARREGAR BM25
# ============================================================

print("Carregando índice BM25...")

with open(
    ARQUIVO_BM25,
    "rb"
) as arquivo:

    bm25 = pickle.load(arquivo)


with open(
    ARQUIVO_DOCUMENTOS_BM25,
    "r",
    encoding="utf-8"
) as arquivo:

    documentos_bm25 = json.load(arquivo)


print("[OK] BM25 carregado.")


# ============================================================
# CARREGAR CHROMA
# ============================================================

print("Carregando ChromaDB...")

client = chromadb.PersistentClient(
    path=str(PASTA_CHROMA)
)

collection = client.get_collection(
    name=NOME_COLECAO
)

print(
    f"[OK] Chroma carregado "
    f"({collection.count()} registros)."
)


# ============================================================
# CARREGAR MODELO DE EMBEDDING
# ============================================================

print("Carregando modelo de embeddings...")

modelo = SentenceTransformer(
    MODELO_EMBEDDING
)

print("[OK] Modelo carregado.")


# ============================================================
# BUSCA BM25
# ============================================================

def busca_bm25(
    pergunta: str,
    top_k: int = TOP_K_BM25
):

    tokens_pergunta = tokenizar(
        pergunta
    )

    scores = bm25.get_scores(
        tokens_pergunta
    )

    ranking = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )

    resultados = []

    for posicao, (indice, score) in enumerate(
        ranking[:top_k],
        start=1
    ):

        documento = documentos_bm25[indice]

        resultados.append(
            {
                "chunk_id": documento["chunk_id"],
                "rank": posicao,
                "score_bm25": float(score),
                "arquivo": documento["arquivo"],
                "categoria": documento["categoria"],
                "texto": documento["texto"]
            }
        )

    return resultados


# ============================================================
# BUSCA VETORIAL
# ============================================================

def busca_vetorial(
    pergunta: str,
    top_k: int = TOP_K_VECTOR
):

    embedding_pergunta = modelo.encode(
        pergunta,
        normalize_embeddings=True
    ).tolist()

    resultado = collection.query(
        query_embeddings=[
            embedding_pergunta
        ],
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    resultados = []

    for posicao in range(
        len(resultado["ids"][0])
    ):

        metadata = (
            resultado["metadatas"][0][posicao]
        )

        distancia = (
            resultado["distances"][0][posicao]
        )

        resultados.append(
            {
                "chunk_id": metadata["chunk_id"],
                "rank": posicao + 1,
                "distancia": float(distancia),
                "arquivo": metadata["arquivo"],
                "categoria": metadata["categoria"],
                "texto": resultado["documents"][0][posicao]
            }
        )

    return resultados


# ============================================================
# RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    resultados_bm25,
    resultados_vetoriais,
    rrf_k=RRF_K
):

    combinados = {}

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    for resultado in resultados_bm25:

        chunk_id = resultado["chunk_id"]

        if chunk_id not in combinados:

            combinados[chunk_id] = {
                "chunk_id": chunk_id,
                "rrf_score": 0.0,
                "rank_bm25": None,
                "rank_vector": None,
                "score_bm25": None,
                "distancia_vector": None,
                "arquivo": resultado["arquivo"],
                "categoria": resultado["categoria"],
                "texto": resultado["texto"]
            }

        combinados[chunk_id]["rank_bm25"] = (
            resultado["rank"]
        )

        combinados[chunk_id]["score_bm25"] = (
            resultado["score_bm25"]
        )

        combinados[chunk_id]["rrf_score"] += (
            1 / (rrf_k + resultado["rank"])
        )


    # --------------------------------------------------------
    # VETORIAL
    # --------------------------------------------------------

    for resultado in resultados_vetoriais:

        chunk_id = resultado["chunk_id"]

        if chunk_id not in combinados:

            combinados[chunk_id] = {
                "chunk_id": chunk_id,
                "rrf_score": 0.0,
                "rank_bm25": None,
                "rank_vector": None,
                "score_bm25": None,
                "distancia_vector": None,
                "arquivo": resultado["arquivo"],
                "categoria": resultado["categoria"],
                "texto": resultado["texto"]
            }

        combinados[chunk_id]["rank_vector"] = (
            resultado["rank"]
        )

        combinados[chunk_id]["distancia_vector"] = (
            resultado["distancia"]
        )

        combinados[chunk_id]["rrf_score"] += (
            1 / (rrf_k + resultado["rank"])
        )


    # --------------------------------------------------------
    # ORDENAR RESULTADOS
    # --------------------------------------------------------

    ranking_final = sorted(
        combinados.values(),
        key=lambda x: x["rrf_score"],
        reverse=True
    )

    return ranking_final


# ============================================================
# BUSCA HÍBRIDA
# ============================================================

def busca_hibrida(
    pergunta: str,
    top_k_final: int = TOP_K_FINAL
):

    resultados_bm25 = busca_bm25(
        pergunta
    )

    resultados_vetoriais = busca_vetorial(
        pergunta
    )

    ranking_rrf = reciprocal_rank_fusion(
        resultados_bm25,
        resultados_vetoriais
    )

    return (
        resultados_bm25,
        resultados_vetoriais,
        ranking_rrf[:top_k_final]
    )


# ============================================================
# EXECUÇÃO INTERATIVA
# ============================================================

print("\n" + "=" * 70)
print("06 - BUSCA HÍBRIDA BM25 + VETORIAL + RRF")
print("=" * 70)


pergunta = input(
    "\nDigite uma pergunta sobre o Flamengo:\n> "
).strip()


if not pergunta:

    print("[ERRO] Pergunta vazia.")
    raise SystemExit(1)


bm25_resultados, vetoriais, finais = (
    busca_hibrida(
        pergunta
    )
)


# ============================================================
# EXIBIR BM25
# ============================================================

print("\n" + "=" * 70)
print("TOP BM25")
print("=" * 70)


for resultado in bm25_resultados:

    print(
        f"\nRank {resultado['rank']} "
        f"| chunk_id={resultado['chunk_id']} "
        f"| score={resultado['score_bm25']:.4f}"
    )

    print(
        f"Arquivo: {resultado['arquivo']}"
    )

    print(
        resultado["texto"][:300]
    )


# ============================================================
# EXIBIR VETORIAL
# ============================================================

print("\n" + "=" * 70)
print("TOP VETORIAL")
print("=" * 70)


for resultado in vetoriais:

    print(
        f"\nRank {resultado['rank']} "
        f"| chunk_id={resultado['chunk_id']} "
        f"| distância={resultado['distancia']:.4f}"
    )

    print(
        f"Arquivo: {resultado['arquivo']}"
    )

    print(
        resultado["texto"][:300]
    )


# ============================================================
# EXIBIR RRF
# ============================================================

print("\n" + "=" * 70)
print("RANKING FINAL - RRF")
print("=" * 70)


for posicao, resultado in enumerate(
    finais,
    start=1
):

    print(
        f"\n{posicao}. chunk_id="
        f"{resultado['chunk_id']}"
    )

    print(
        f"RRF score: "
        f"{resultado['rrf_score']:.6f}"
    )

    print(
        f"Rank BM25: "
        f"{resultado['rank_bm25']}"
    )

    print(
        f"Rank vetorial: "
        f"{resultado['rank_vector']}"
    )

    print(
        f"Arquivo: "
        f"{resultado['arquivo']}"
    )

    print(
        f"Categoria: "
        f"{resultado['categoria']}"
    )

    print("\nTexto:")
    print(
        resultado["texto"]
    )

    print("-" * 70)