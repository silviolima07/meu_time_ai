
#!/usr/bin/env python3
"""Meu Time IA — Experimento 2: RRF ampliado e reranking."""

import csv
import json
import sys
import time
from pathlib import Path

BENCHMARK_RAIZ = Path(__file__).resolve().parent.parent
RAIZ = BENCHMARK_RAIZ.parent.parent
sys.path.insert(0, str(RAIZ))

from sentence_transformers import CrossEncoder
from scripts.rag_core import (
    busca_bm25,
    busca_vetorial,
    reciprocal_rank_fusion,
)

MODELO = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
BENCHMARK = BENCHMARK_RAIZ / "benchmark_v1.0_factual_validado.jsonl"
SAIDA = BENCHMARK_RAIZ / "resultados"
K = 3


def normalizar_id(valor):
    texto = str(valor)
    return texto if texto.startswith("chunk_") else f"chunk_{texto}"


def calcular_metricas(ranking, relevantes):
    ids = [normalizar_id(r["chunk_id"]) for r in ranking[:K]]
    relevantes = set(map(normalizar_id, relevantes))

    acertos = sum(cid in relevantes for cid in ids)
    primeiro = next(
        (i for i, cid in enumerate(ids, 1) if cid in relevantes),
        None,
    )

    return {
        "precision@3": acertos / K,
        "recall@3": acertos / len(relevantes),
        "hit@3": int(acertos > 0),
        "mrr@3": 1 / primeiro if primeiro else 0.0,
        "chunks_recuperados": ",".join(ids),
    }


def carregar_benchmark():
    with BENCHMARK.open(encoding="utf-8") as f:
        registros = [json.loads(l) for l in f if l.strip()]

    if not registros:
        raise ValueError("Benchmark vazio")

    for r in registros:
        if not r["chunks_relevantes"]:
            raise ValueError(f"Sem ground truth: {r['id']}")

    return registros


def avaliar():
    perguntas = carregar_benchmark()

    print("Carregando Cross-Encoder...")
    modelo = CrossEncoder(MODELO, device="cpu")

    linhas = []

    for pergunta in perguntas:
        texto = pergunta["pergunta"]
        relevantes = pergunta["chunks_relevantes"]

        inicio_busca = time.perf_counter()
        bm25 = busca_bm25(texto, top_k=10)
        vetorial = busca_vetorial(texto, top_k=10)
        ranking = reciprocal_rank_fusion(bm25, vetorial)
        latencia_busca = time.perf_counter() - inicio_busca

        # Baseline real: refaz a fusão usando apenas Top 5
        rrf_original = reciprocal_rank_fusion(bm25[:5], vetorial[:5])

        inicio_rerank = time.perf_counter()
        pares = [(texto, item["texto"]) for item in ranking]
        scores = modelo.predict(pares, batch_size=4)

        rerankeados = [
            {**item, "score_reranker": float(score)}
            for item, score in zip(ranking, scores)
        ]
        rerankeados.sort(
            key=lambda item: item["score_reranker"],
            reverse=True,
        )
        latencia_rerank = time.perf_counter() - inicio_rerank

        metodos = {
            "RRF_baseline_5": (rrf_original, None),
            "RRF_ampliado_10": (ranking, latencia_busca),
            "RRF_reranker_10": (
                rerankeados,
                latencia_busca + latencia_rerank,
            ),
        }

        for metodo, (resultados, latencia) in metodos.items():
            linhas.append({
                "pergunta_id": pergunta["id"],
                "metodo": metodo,
                "ground_truth": ",".join(
                    map(normalizar_id, relevantes)
                ),
                **calcular_metricas(resultados, relevantes),
                "latencia_segundos": (
                    round(latencia, 4) if latencia is not None else ""
                ),
            })

        print(
            f"{pergunta['id']}: OK "
            f"| busca={latencia_busca:.3f}s "
            f"| reranker={latencia_rerank:.3f}s"
        )

    return linhas


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    linhas = avaliar()

    arquivo_csv = SAIDA / "reranker_v1.0_detalhes.csv"
    with arquivo_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=linhas[0].keys())
        writer.writeheader()
        writer.writerows(linhas)

    resumo = {}
    metricas = ("precision@3", "recall@3", "hit@3", "mrr@3")

    for metodo in (
        "RRF_baseline_5",
        "RRF_ampliado_10",
        "RRF_reranker_10",
    ):
        registros = [r for r in linhas if r["metodo"] == metodo]
        resumo[metodo] = {
            m: sum(r[m] for r in registros) / len(registros)
            for m in metricas
        }

        tempos = [
            r["latencia_segundos"] for r in registros
            if isinstance(r["latencia_segundos"], (int, float))
        ]
        resumo[metodo]["latencia_media_segundos"] = (
            sum(tempos) / len(tempos) if tempos else None
        )

    arquivo_json = SAIDA / "reranker_v1.0_resumo.json"
    with arquivo_json.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "benchmark": "factual_v1.0",
                "modelo_reranker": MODELO,
                "top_k_final": K,
                "perguntas": len(linhas) // 3,
                "resultados": resumo,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 65)
    print("EXPERIMENTO 2 — COMPARAÇÃO")
    print("=" * 65)

    for metodo, dados in resumo.items():
        print(f"\n{metodo}")
        for metrica in metricas:
            print(f"  {metrica}: {dados[metrica]:.2%}")
        tempo = dados["latencia_media_segundos"]
        if tempo is not None:
            print(f"  Latência média: {tempo:.3f}s")

    print(f"\nCSV:  {arquivo_csv.relative_to(RAIZ)}")
    print(f"JSON: {arquivo_json.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
