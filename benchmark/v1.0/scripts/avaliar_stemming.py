#!/usr/bin/env python3
"""
Meu Time IA — Experimento de stemming no BM25.

Compara:
- BM25 original
- BM25 com stemming português
- RRF original
- RRF com BM25 stemming

Não modifica índices, corpus ou benchmark v1.0.
"""

import csv
import sys
from pathlib import Path

from nltk.stem.snowball import SnowballStemmer
from rank_bm25 import BM25Okapi

BENCHMARK_RAIZ = Path(__file__).resolve().parent.parent
RAIZ = BENCHMARK_RAIZ.parent.parent
sys.path.insert(0, str(RAIZ))

from scripts import rag_core as rag
from avaliar_recuperacao import (
    carregar_perguntas,
    calcular_metricas,
)

SAIDA = BENCHMARK_RAIZ / "resultados"
SAIDA.mkdir(parents=True, exist_ok=True)

K = 3
stemmer = SnowballStemmer("portuguese")


def tokenizar_stem(texto):
    return [
        stemmer.stem(token)
        for token in rag.tokenizar(texto)
    ]


def criar_indice_stem():
    documentos = rag.documentos_bm25

    corpus = [
        tokenizar_stem(doc["texto"])
        for doc in documentos
    ]

    return BM25Okapi(corpus)


def buscar_stem(indice, pergunta, top_k=5):
    scores = indice.get_scores(
        tokenizar_stem(pergunta)
    )

    ranking = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )

    resultados = []

    for posicao, (indice_doc, score) in enumerate(
        ranking[:top_k], 1
    ):
        documento = rag.documentos_bm25[indice_doc]

        resultados.append({
            "chunk_id": documento["chunk_id"],
            "rank": posicao,
            "score_bm25": float(score),
            "arquivo": documento["arquivo"],
            "categoria": documento["categoria"],
            "texto": documento["texto"],
        })

    return resultados


def avaliar():
    indice_stem = criar_indice_stem()
    perguntas = carregar_perguntas()
    resultados = []

    for pergunta in perguntas:
        qid = pergunta["id"]
        texto = pergunta["pergunta"]
        relevantes = pergunta["chunks_relevantes"]

        bm25_original = rag.busca_bm25(
            texto, top_k=5
        )

        bm25_stem = buscar_stem(
            indice_stem, texto, top_k=5
        )

        vetorial = rag.busca_vetorial(
            texto, top_k=5
        )

        rrf_original = rag.reciprocal_rank_fusion(
            bm25_original, vetorial
        )

        rrf_stem = rag.reciprocal_rank_fusion(
            bm25_stem, vetorial
        )

        metodos = {
            "BM25_original": bm25_original,
            "BM25_stemming": bm25_stem,
            "RRF_original": rrf_original,
            "RRF_stemming": rrf_stem,
        }

        for metodo, ranking in metodos.items():
            recuperados = [
                f"chunk_{item['chunk_id']}"
                for item in ranking[:K]
            ]

            metricas = calcular_metricas(
                recuperados, relevantes
            )

            resultados.append({
                "pergunta_id": qid,
                "metodo": metodo,
                "chunks_relevantes": ",".join(relevantes),
                "chunks_recuperados": ",".join(recuperados),
                **metricas,
            })

        print(f"{qid}: avaliada")

    return resultados


def main():
    resultados = avaliar()

    caminho = SAIDA / "stemming_v1.0_detalhes.csv"

    with caminho.open(
        "w", encoding="utf-8", newline=""
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=resultados[0].keys()
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    print("\nRESULTADOS — MACRO-MÉDIAS")
    print("=" * 70)

    for metodo in (
        "BM25_original",
        "BM25_stemming",
        "RRF_original",
        "RRF_stemming",
    ):
        registros = [
            r for r in resultados
            if r["metodo"] == metodo
        ]

        medias = {
            metrica: sum(
                r[metrica] for r in registros
            ) / len(registros)
            for metrica in (
                "precision@3",
                "recall@3",
                "hit@3",
                "reciprocal_rank",
            )
        }

        print(
            f"{metodo:16} "
            f"P@3={medias['precision@3']:.4f} "
            f"R@3={medias['recall@3']:.4f} "
            f"Hit@3={medias['hit@3']:.4f} "
            f"MRR@3={medias['reciprocal_rank']:.4f}"
        )

    print(f"\nCSV: {caminho}")


if __name__ == "__main__":
    main()
