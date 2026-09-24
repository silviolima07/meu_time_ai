from pathlib import Path
from datetime import datetime

import os
import json
import pickle
import re
import unicodedata
import requests
import chromadb

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(ROOT / ".env")


# ------------------------------------------------------------
# Groq
# ------------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)

GROQ_MODEL =  LLM_MODEL


# ------------------------------------------------------------
# BM25
# ------------------------------------------------------------

PASTA_BM25 = (
    ROOT
    / "dados_processados"
    / "bm25"
)

ARQUIVO_BM25 = (
    PASTA_BM25
    / "bm25.pkl"
)

ARQUIVO_DOCUMENTOS_BM25 = (
    PASTA_BM25
    / "documentos_bm25.json"
)


# ------------------------------------------------------------
# ChromaDB
# ------------------------------------------------------------

PASTA_CHROMA = ROOT / "chroma_db"

NOME_COLECAO = "flamengo"


# ------------------------------------------------------------
# Embeddings
# ------------------------------------------------------------

MODELO_EMBEDDING = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ------------------------------------------------------------
# Retrieval
# ------------------------------------------------------------

TOP_K_BM25 = 5
TOP_K_VECTOR = 5
TOP_K_FINAL = 3

RRF_K = 60


# ------------------------------------------------------------
# Logs
# ------------------------------------------------------------

PASTA_LOGS = ROOT / "logs"

PASTA_LOGS.mkdir(
    parents=True,
    exist_ok=True
)

ARQUIVO_LOG = (
    PASTA_LOGS
    / "rag_interacoes.jsonl"
)


# ============================================================
# VALIDAÇÕES
# ============================================================

if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY não encontrada no .env"
    )


if not ARQUIVO_BM25.exists():

    raise RuntimeError(
        "Índice BM25 não encontrado."
    )


if not ARQUIVO_DOCUMENTOS_BM25.exists():

    raise RuntimeError(
        "documentos_bm25.json não encontrado."
    )


# ============================================================
# TOKENIZAÇÃO
# ============================================================

def remover_acentos(texto: str) -> str:

    texto_normalizado = unicodedata.normalize(
        "NFD",
        texto
    )

    return "".join(
        caractere
        for caractere in texto_normalizado
        if unicodedata.category(
            caractere
        ) != "Mn"
    )


def tokenizar(texto: str) -> list[str]:

    texto = texto.lower()

    texto = remover_acentos(
        texto
    )

    return re.findall(
        r"\b[a-z0-9]+\b",
        texto
    )


# ============================================================
# CARREGAR BM25
# ============================================================

print("Carregando BM25...")

with open(
    ARQUIVO_BM25,
    "rb"
) as arquivo:

    bm25 = pickle.load(
        arquivo
    )


with open(
    ARQUIVO_DOCUMENTOS_BM25,
    "r",
    encoding="utf-8"
) as arquivo:

    documentos_bm25 = json.load(
        arquivo
    )


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

print(
    "Carregando modelo de embeddings..."
)

modelo = SentenceTransformer(
    MODELO_EMBEDDING
)

print(
    "[OK] Modelo carregado."
)


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

        documento = (
            documentos_bm25[indice]
        )

        resultados.append(
            {
                "chunk_id":
                    documento["chunk_id"],

                "rank":
                    posicao,

                "score_bm25":
                    float(score),

                "arquivo":
                    documento["arquivo"],

                "categoria":
                    documento["categoria"],

                "texto":
                    documento["texto"]
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
        len(
            resultado["ids"][0]
        )
    ):

        metadata = (
            resultado[
                "metadatas"
            ][0][posicao]
        )

        distancia = (
            resultado[
                "distances"
            ][0][posicao]
        )

        resultados.append(
            {
                "chunk_id":
                    metadata["chunk_id"],

                "rank":
                    posicao + 1,

                "distancia":
                    float(distancia),

                "arquivo":
                    metadata["arquivo"],

                "categoria":
                    metadata["categoria"],

                "texto":
                    resultado[
                        "documents"
                    ][0][posicao]
            }
        )

    return resultados


# ============================================================
# RRF
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

        chunk_id = (
            resultado["chunk_id"]
        )


        if chunk_id not in combinados:

            combinados[
                chunk_id
            ] = {
                "chunk_id":
                    chunk_id,

                "rrf_score":
                    0.0,

                "rank_bm25":
                    None,

                "rank_vector":
                    None,

                "score_bm25":
                    None,

                "distancia_vector":
                    None,

                "arquivo":
                    resultado["arquivo"],

                "categoria":
                    resultado["categoria"],

                "texto":
                    resultado["texto"]
            }


        combinados[
            chunk_id
        ]["rank_bm25"] = (
            resultado["rank"]
        )


        combinados[
            chunk_id
        ]["score_bm25"] = (
            resultado["score_bm25"]
        )


        combinados[
            chunk_id
        ]["rrf_score"] += (
            1 / (
                rrf_k
                + resultado["rank"]
            )
        )


    # --------------------------------------------------------
    # VETORIAL
    # --------------------------------------------------------

    for resultado in resultados_vetoriais:

        chunk_id = (
            resultado["chunk_id"]
        )


        if chunk_id not in combinados:

            combinados[
                chunk_id
            ] = {
                "chunk_id":
                    chunk_id,

                "rrf_score":
                    0.0,

                "rank_bm25":
                    None,

                "rank_vector":
                    None,

                "score_bm25":
                    None,

                "distancia_vector":
                    None,

                "arquivo":
                    resultado["arquivo"],

                "categoria":
                    resultado["categoria"],

                "texto":
                    resultado["texto"]
            }


        combinados[
            chunk_id
        ]["rank_vector"] = (
            resultado["rank"]
        )


        combinados[
            chunk_id
        ]["distancia_vector"] = (
            resultado["distancia"]
        )


        combinados[
            chunk_id
        ]["rrf_score"] += (
            1 / (
                rrf_k
                + resultado["rank"]
            )
        )


    ranking_final = sorted(
        combinados.values(),
        key=lambda x: x[
            "rrf_score"
        ],
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


    ranking = reciprocal_rank_fusion(
        resultados_bm25,
        resultados_vetoriais
    )


    return ranking[
        :top_k_final
    ]


# ============================================================
# MONTAR CONTEXTO
# ============================================================

def montar_contexto(
    resultados
):

    blocos = []


    for posicao, resultado in enumerate(
        resultados,
        start=1
    ):

        bloco = (
            f"[Fonte {posicao}]\n"
            f"Arquivo: "
            f"{resultado['arquivo']}\n"

            f"Categoria: "
            f"{resultado['categoria']}\n"

            f"Conteúdo:\n"
            f"{resultado['texto']}"
        )


        blocos.append(
            bloco
        )


    return "\n\n".join(
        blocos
    )


# ============================================================
# CONSULTAR GROQ
# ============================================================

def perguntar_llm(
    pergunta: str,
    contexto: str
):

    prompt_sistema = """
Você é o Meu Time IA, um assistente especializado no Flamengo.

Responda somente com base no contexto fornecido.

Regras:

1. Não invente informações.
2. Se o contexto não tiver informação suficiente,
   diga claramente que a base de conhecimento
   não possui dados suficientes.
3. Responda em português.
4. Seja claro e objetivo.
5. Use datas quando forem importantes.
6. Para informações atuais, respeite a data
   existente no contexto.
7. Não mencione chunks, embeddings, BM25,
   RRF ou banco vetorial para o usuário.
"""


    prompt_usuario = f"""
CONTEXTO:

{contexto}


PERGUNTA:

{pergunta}


Responda à pergunta usando apenas
o contexto fornecido.
"""


    response = requests.post(
        GROQ_URL,

        headers={
            "Authorization":
                f"Bearer {GROQ_API_KEY}",

            "Content-Type":
                "application/json"
        },

        json={
            "model":
                GROQ_MODEL,

            "messages": [
                {
                    "role":
                        "system",

                    "content":
                        prompt_sistema
                },

                {
                    "role":
                        "user",

                    "content":
                        prompt_usuario
                }
            ],

            "temperature":
                0.2
        },

        timeout=60
    )


    response.raise_for_status()


    dados = response.json()


    return (
        dados[
            "choices"
        ][0][
            "message"
        ][
            "content"
        ]
    )


# ============================================================
# LOG DE AUDITORIA
# ============================================================

def salvar_log(
    pergunta: str,
    resposta: str,
    resultados: list
):

    evidencias = []


    for resultado in resultados:

        evidencias.append(
            {
                "chunk_id":
                    resultado["chunk_id"],

                "arquivo":
                    resultado["arquivo"],

                "categoria":
                    resultado["categoria"],

                "rrf_score":
                    resultado["rrf_score"],

                "rank_bm25":
                    resultado.get(
                        "rank_bm25"
                    ),

                "rank_vector":
                    resultado.get(
                        "rank_vector"
                    ),

                "score_bm25":
                    resultado.get(
                        "score_bm25"
                    ),

                "distancia_vector":
                    resultado.get(
                        "distancia_vector"
                    ),

                "texto":
                    resultado["texto"]
            }
        )


    registro = {
        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "pergunta":
            pergunta,

        "resposta":
            resposta,

        "evidencias":
            evidencias
    }


    with open(
        ARQUIVO_LOG,
        "a",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(
            json.dumps(
                registro,
                ensure_ascii=False
            )
            + "\n"
        )
