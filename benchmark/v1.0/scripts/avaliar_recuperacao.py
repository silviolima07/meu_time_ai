
#!/usr/bin/env python3
"""
Meu Time IA — Avaliação da recuperação v1.0.

Compara BM25, busca vetorial e RRF utilizando
o ground truth factual validado.

Não chama o LLM e não altera os índices.
"""

import csv
import json
import sys
from pathlib import Path

BENCHMARK_RAIZ = Path(__file__).resolve().parent.parent
RAIZ = BENCHMARK_RAIZ.parent.parent
sys.path.insert(0, str(RAIZ))

from scripts.rag_core import (
    busca_bm25,
    busca_vetorial,
    reciprocal_rank_fusion,
)

BENCHMARK = (
    BENCHMARK_RAIZ
    / "benchmark_v1.0_factual_validado.jsonl"
)

SAIDA = BENCHMARK_RAIZ / "resultados"
SAIDA.mkdir(parents=True, exist_ok=True)

K = 3


def carregar_perguntas():
    with BENCHMARK.open(encoding="utf-8") as arquivo:
        return [
            json.loads(linha)
            for linha in arquivo
            if linha.strip()
        ]


def calcular_metricas(recuperados, relevantes):
    recuperados = recuperados[:K]
    relevantes = set(relevantes)

    acertos = [
        chunk_id
        for chunk_id in recuperados
        if chunk_id in relevantes
    ]

    precision = len(acertos) / K
    recall = len(acertos) / len(relevantes)
    hit = int(bool(acertos))

    reciprocal_rank = 0.0

    for posicao, chunk_id in enumerate(recuperados, 1):
        if chunk_id in relevantes:
            reciprocal_rank = 1 / posicao
            break

    return {
        "precision@3": precision,
        "recall@3": recall,
        "hit@3": hit,
        "reciprocal_rank": reciprocal_rank,
    }


def avaliar():
    perguntas = carregar_perguntas()
    resultados = []

    for pergunta in perguntas:
        qid = pergunta["id"]
        texto = pergunta["pergunta"]
        relevantes = pergunta["chunks_relevantes"]

        bm25 = busca_bm25(texto, top_k=5)
        vetorial = busca_vetorial(texto, top_k=5)

        rrf = reciprocal_rank_fusion(bm25, vetorial)

        metodos = {
            "BM25": bm25,
            "Vetorial": vetorial,
            "RRF": rrf,
        }

        for metodo, ranking in metodos.items():
            recuperados = [
                f"chunk_{item['chunk_id']}"
                for item in ranking[:K]
            ]

            metricas = calcular_metricas(
                recuperados,
                relevantes
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


def salvar_csv(resultados):
    caminho = SAIDA / "recuperacao_v1.0_detalhes.csv"

    with caminho.open(
        "w", encoding="utf-8", newline=""
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=resultados[0].keys()
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    return caminho


def calcular_medias(resultados):
    resumo = {}

    for metodo in ("BM25", "Vetorial", "RRF"):
        registros = [
            r for r in resultados
            if r["metodo"] == metodo
        ]

        resumo[metodo] = {
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

    return resumo


def main():
    resultados = avaliar()
    caminho_csv = salvar_csv(resultados)
    resumo = calcular_medias(resultados)

    caminho_json = (
        SAIDA / "recuperacao_v1.0_resumo.json"
    )

    with caminho_json.open(
        "w", encoding="utf-8"
    ) as arquivo:
        json.dump(
            {
                "benchmark": "factual_v1.0",
                "top_k": K,
                "numero_perguntas": 15,
                "metodos": resumo,
            },
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 60)
    print("RESULTADOS — BENCHMARK DE RECUPERAÇÃO")
    print("=" * 60)

    for metodo, metricas in resumo.items():
        print(f"\n{metodo}")
        print(f"  Precision@3: {metricas['precision@3']:.2%}")
        print(f"  Recall@3:    {metricas['recall@3']:.2%}")
        print(f"  Hit@3:       {metricas['hit@3']:.2%}")
        print(f"  MRR:         {metricas['reciprocal_rank']:.4f}")

    print(f"\nDetalhes: {caminho_csv.relative_to(RAIZ)}")
    print(f"Resumo:   {caminho_json.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
