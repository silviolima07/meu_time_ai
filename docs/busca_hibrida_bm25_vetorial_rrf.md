# Estratégia de Busca Híbrida — BM25 + Busca Vetorial + RRF

## 1. Objetivo

A busca híbrida combina:

- **BM25**: relevância lexical.
- **Busca vetorial**: proximidade semântica.
- **RRF (Reciprocal Rank Fusion)**: fusão dos rankings.

Fluxo:

```text
Pergunta
   ├── BM25 -> Top 5
   └── Vetorial -> Top 5
            ↓
           RRF
            ↓
         Top 3
            ↓
           LLM
```

## 2. BM25

O BM25 usa frequência de termos, raridade no corpus e tamanho dos chunks.

O índice é criado antes da pergunta:

```python
bm25 = BM25Okapi(corpus_tokenizado)
```

### Tokenização

```python
def remover_acentos(texto: str) -> str:
    texto_normalizado = unicodedata.normalize("NFD", texto)
    return "".join(
        c for c in texto_normalizado
        if unicodedata.category(c) != "Mn"
    )

def tokenizar(texto: str) -> list[str]:
    texto = remover_acentos(texto.lower())
    return re.findall(r"\b[a-z0-9]+\b", texto)
```

### Busca BM25

```python
def busca_bm25(pergunta: str, top_k: int = 5):
    tokens_pergunta = tokenizar(pergunta)
    scores = bm25.get_scores(tokens_pergunta)

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

        resultados.append({
            "chunk_id": documento["chunk_id"],
            "rank": posicao,
            "score_bm25": float(score),
            "arquivo": documento["arquivo"],
            "categoria": documento["categoria"],
            "texto": documento["texto"]
        })

    return resultados
```

### Métrica BM25

Não existe valor máximo fixo.

Regra:

```text
maior score BM25 = melhor resultado
```

Exemplo:

```text
chunk 65 -> 11.84
chunk 68 -> 9.51
chunk 66 -> 6.17
```

O valor só deve ser comparado dentro da mesma consulta.

## 3. Busca Vetorial

Cada chunk vira um embedding.

Modelo usado:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### Consulta vetorial

```python
def busca_vetorial(pergunta: str, top_k: int = 5):

    embedding_pergunta = modelo.encode(
        pergunta,
        normalize_embeddings=True
    ).tolist()

    resultado = collection.query(
        query_embeddings=[embedding_pergunta],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    resultados = []

    for posicao in range(len(resultado["ids"][0])):

        metadata = resultado["metadatas"][0][posicao]
        distancia = resultado["distances"][0][posicao]

        resultados.append({
            "chunk_id": metadata["chunk_id"],
            "rank": posicao + 1,
            "distancia": float(distancia),
            "arquivo": metadata["arquivo"],
            "categoria": metadata["categoria"],
            "texto": resultado["documents"][0][posicao]
        })

    return resultados
```

### Métrica vetorial

O ChromaDB foi configurado com:

```python
metadata={"hnsw:space": "cosine"}
```

Regra:

```text
menor distância = melhor
```

Exemplo:

```text
0.16 -> mais próximo
0.19 -> próximo
0.30 -> menos próximo
```

Pode-se calcular uma similaridade aproximada:

```python
similaridade = 1 - distancia
```

Exemplo:

```text
distância = 0.1629
similaridade ≈ 0.8371 = 83,71%
```

Isso não é probabilidade de acerto; é proximidade vetorial.

## 4. Por que não somar BM25 e distância vetorial

As escalas são diferentes.

Exemplo:

```text
BM25 = 11.84
distância vetorial = 0.16
```

Somar os dois não faz sentido diretamente.

Por isso usamos RRF.

## 5. RRF — Reciprocal Rank Fusion

Fórmula:

```text
RRF(d) = Σ 1 / (k + rank(d))
```

No projeto:

```python
RRF_K = 60
```

### Função RRF

```python
def reciprocal_rank_fusion(
    resultados_bm25,
    resultados_vetoriais,
    rrf_k=60
):
    combinados = {}

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

        combinados[chunk_id]["rank_bm25"] = resultado["rank"]
        combinados[chunk_id]["score_bm25"] = resultado["score_bm25"]
        combinados[chunk_id]["rrf_score"] += 1 / (
            rrf_k + resultado["rank"]
        )

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

        combinados[chunk_id]["rank_vector"] = resultado["rank"]
        combinados[chunk_id]["distancia_vector"] = resultado["distancia"]
        combinados[chunk_id]["rrf_score"] += 1 / (
            rrf_k + resultado["rank"]
        )

    return sorted(
        combinados.values(),
        key=lambda x: x["rrf_score"],
        reverse=True
    )
```

## 6. Busca Híbrida

```python
TOP_K_BM25 = 5
TOP_K_VECTOR = 5
TOP_K_FINAL = 3
```

```python
def busca_hibrida(pergunta: str, top_k_final: int = TOP_K_FINAL):

    resultados_bm25 = busca_bm25(pergunta)
    resultados_vetoriais = busca_vetorial(pergunta)

    ranking_rrf = reciprocal_rank_fusion(
        resultados_bm25,
        resultados_vetoriais
    )

    return (
        resultados_bm25,
        resultados_vetoriais,
        ranking_rrf[:top_k_final]
    )
```

## 7. Exemplo real

Pergunta:

```text
Quantas Libertadores o Flamengo tem?
```

BM25:

```text
chunk 65
score = 11.8415
rank = 1
```

Vetorial:

```text
chunk 65
distância = 0.1629
rank = 1
```

RRF:

```text
chunk 65
rank BM25 = 1
rank vetorial = 1
RRF score = 0.032787
```

O mesmo chunk venceu nas duas buscas.

## 8. Resumo das métricas

| Métrica | Interpretação | Melhor valor |
|---|---|---|
| BM25 Score | Relevância lexical | Maior |
| Distância vetorial | Distância semântica | Menor |
| Similaridade aproximada | `1 - distância` | Maior |
| RRF Score | Fusão das posições | Maior |

## 9. Vantagem da busca híbrida

BM25 é forte em termos exatos:

```text
Libertadores
Zico
1981
```

A busca vetorial é forte em significado:

```text
goleador ≈ artilheiro
```

O RRF combina os dois rankings sem precisar normalizar scores incompatíveis.

## 10. Pipeline do projeto

```text
01_carregar_documentos.py
        ↓
02_criar_chunks.py
        ↓
03_gerar_embeddings.py
        ↓
04_salvar_chroma.py
        ↓
05_criar_indice_bm25.py
        ↓
06_busca_hibrida.py
        ↓
Top 3 chunks
        ↓
LLM
```

A estratégia separa claramente:

```text
recuperação da informação
```

de:

```text
geração da resposta
```
