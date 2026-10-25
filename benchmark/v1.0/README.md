# Meu Time IA — Benchmark RAG v1.0

**Data:** 25/10/2026
**Ambiente original:** homologação
**Status:** avaliação de recuperação concluída
**Produção:** pipeline original preservado

## Objetivo

Avaliar a qualidade da recuperação de informações do RAG
Meu Time IA e investigar alternativas de melhoria considerando
precisão, cobertura, latência e complexidade computacional.

## Base de avaliação

- 72 chunks provenientes de quatro documentos Markdown.
- 15 perguntas factuais validadas.
- 24 associações entre perguntas e chunks relevantes.
- Avaliação dos três primeiros resultados recuperados (K=3).

## Métricas

- Precision@3
- Recall@3
- Hit@3
- MRR@3

## Resultados da recuperação

| Método | Precision@3 | Recall@3 | Hit@3 | MRR@3 |
|---|---:|---:|---:|---:|
| BM25 | 37,78% | 80,00% | 93,33% | 81,11% |
| Busca vetorial | 31,11% | 63,33% | 80,00% | 67,78% |
| RRF original | 37,78% | 80,00% | 93,33% | 77,78% |
| RRF com stemming | 42,22% | 85,56% | 93,33% | 76,67% |

O stemming apresentou melhorias em algumas métricas agregadas,
mas não foi incorporado ao pipeline de produção.

## Experimento com reranking

Foi avaliado o modelo:

`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`

O reranking não apresentou melhoria consistente nas métricas
de recuperação e aumentou a latência média observada.

Por esse motivo, não foi incorporado à produção.

## Decisões arquiteturais

1. Preservar BM25 + busca vetorial + RRF como baseline.
2. Não adicionar reranking sem benefício comprovado.
3. Manter stemming como alternativa experimental.
4. Priorizar respostas fundamentadas no contexto recuperado.
5. Permitir abstenção quando não houver evidências suficientes.
6. Manter perguntas desafiadoras no benchmark sem otimizar
   todo o sistema exclusivamente para casos pouco frequentes.

## Organização

- `docs/`: documentação técnica, metodologia e diagrama.
- `scripts/`: implementações dos avaliadores.
- `corpus/`: corpus versionado utilizado nos experimentos.
- `resultados/`: arquivos CSV e JSON com as métricas.
- `benchmark_v1.0_factual_validado.jsonl`: perguntas e ground truth.

## Ambiente experimental

Bibliotecas adicionais utilizadas:

- sentence-transformers==6.0.1
- nltk==3.10.4
- rank-bm25==0.2.2

Os avaliadores dependem também de `scripts/rag_core.py`
e das demais dependências do projeto Meu Time IA.

## Execução

A partir da raiz do projeto, em ambiente isolado com as
dependências instaladas e os índices RAG disponíveis:

```bash
python benchmark/v1.0/scripts/avaliar_recuperacao.py
python benchmark/v1.0/scripts/avaliar_reranker.py
python benchmark/v1.0/scripts/avaliar_stemming.py

```

A execução recalcula as métricas e pode sobrescrever arquivos
em `benchmark/v1.0/resultados/`. Recomenda-se utilizar uma
cópia de testes, não o ambiente de produção.

A integração básica do avaliador de recuperação com o núcleo
RAG foi verificada. A reprodução completa dos três experimentos
ainda não foi validada.

## Documentação completa

Consulte o [relatório técnico](docs/benchmark_meu_time_ia_v1_0.md)
para metodologia, resultados, investigação da Q006 e limitações.

## Próxima etapa

Avaliar a qualidade das respostas geradas pela LLM,
incluindo fidelidade ao contexto, correção factual,
completude e comportamento de abstenção.
