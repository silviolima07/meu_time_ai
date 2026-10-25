# Meu Time IA — Benchmark de Recuperação RAG v1.0

**Data da consolidação:** 25 de outubro de 2026
**Ambiente:** homologação (`meu_time_ai_homolog`)
**Situação:** benchmark de recuperação concluído; avaliação sistemática da geração ainda pendente.

## 1. Objetivo e escopo

Avaliar a recuperação de evidências do assistente Telegram **Meu Time IA**, especializado no Flamengo, por meio de um pipeline RAG híbrido. O objetivo não é maximizar uma única métrica, mas encontrar um equilíbrio entre relevância dos trechos recuperados, fidelidade factual da resposta, latência e complexidade operacional.

Esta versão preserva o pipeline original como **baseline v1.0**. Os experimentos de reranking, stemming e variação de consultas não foram incorporados à produção. Não se deve interpretar resultados de 15 perguntas como garantia de desempenho para todos os usuários ou domínios.

## 2. Arquitetura avaliada

1. Corpus de **72 chunks**, provenientes de **quatro documentos Markdown**; cópia de referência: `benchmarks/corpus/corpus_v1.0.jsonl`.
2. Recuperação lexical **BM25**, `TOP_K_BM25=5`.
3. Recuperação semântica com embeddings e **ChromaDB**, `TOP_K_VECTOR=5`.
4. Fusão **Reciprocal Rank Fusion (RRF)**, `RRF_K=60`.
5. Seleção dos **três** primeiros resultados (`TOP_K_FINAL=3`) para montar o contexto, identificado como `[Fonte 1]`, `[Fonte 2]` e `[Fonte 3]`, com arquivo, categoria e texto.
6. Geração com **Groq**, modelo `openai/gpt-oss-20b`, temperatura `0.2`. A chamada à LLM não integra a medição das métricas de recuperação deste benchmark.

A pontuação RRF de um documento é a soma de `1/(60 + posição)` em cada lista na qual aparece. A fusão utiliza **posições**, não diretamente os scores do BM25 ou distâncias vetoriais. Documentos ausentes do top 5 de ambos os métodos não participam da fusão.

## 3. Ground truth e metodologia

O arquivo `benchmarks/benchmark_v1.0_factual_validado.jsonl` contém **15 perguntas factuais** (`Q001` a `Q015`) e **24 associações pergunta–chunk relevante**. Cada registro contém `id`, `pergunta` e `chunks_relevantes`. A quantidade de chunks relevantes **varia conforme a pergunta**.

A relevância do ground truth foi validada pelo critério de **suficiência**: um chunk relevante deve conter evidência capaz de sustentar a resposta à pergunta, e não apenas mencionar o assunto. Esse critério precisa ser distinguido da mera proximidade temática.

Para cada pergunta, os IDs recuperados são normalizados como `chunk_N` e comparados aos IDs relevantes. Calculam-se as métricas individualmente e, em seguida, sua **macro-média não ponderada** entre as 15 perguntas. Assim, perguntas com um ou três chunks relevantes contribuem com o mesmo peso para a média, embora o denominador de Recall@3 varie.

### 3.1 Métricas

Sejam `R_q` o conjunto de chunks relevantes para a pergunta `q`, `T_q@K` os primeiros K chunks recuperados e `rank_q` a posição do primeiro relevante recuperado:

- **Precision@K** = `|T_q@K ∩ R_q| / K`. Mede a fração dos K resultados que são relevantes.
- **Recall@K** = `|T_q@K ∩ R_q| / |R_q|`. Mede a proporção de evidências relevantes recuperadas.
- **Hit@K** = `1` se pelo menos um relevante estiver entre os K primeiros; caso contrário, `0`.
- **Reciprocal Rank@K** = `1/rank_q` se houver um relevante entre os K primeiros; caso contrário, `0`.
- **MRR@K** = média dos Reciprocal Ranks das perguntas.

Para cada métrica, a macro-média é `(soma dos valores por pergunta) / 15`. Todos os resultados a seguir usam **K=3**.

**Exemplo de denominadores:** se uma pergunta possui três chunks relevantes e o sistema recupera um deles no top 3, então Precision@3 = 1/3 e Recall@3 = 1/3. Se outra pergunta possui apenas um chunk relevante e ele aparece no top 3, Precision@3 continua 1/3, mas Recall@3 = 1. Hit@3 é 1 nos dois casos. O MRR depende da posição do primeiro acerto.

As métricas de recuperação **não medem**, isoladamente, veracidade, completude ou fundamentação da resposta final da LLM.

## 4. Baseline v1.0 — resultados de recuperação

| Método | Precision@3 | Recall@3 | Hit@3 | MRR@3 |
|---|---:|---:|---:|---:|
| BM25 | 37,78% | 80,00% | 93,33% | 81,11% |
| Busca vetorial | 31,11% | 63,33% | 80,00% | 67,78% |
| **RRF original (5+5 → 3)** | **37,78%** | **80,00%** | **93,33%** | **77,78%** |

O BM25 apresentou MRR ligeiramente maior que o RRF nesta amostra; isso não implica superioridade geral. O **RRF original foi mantido como baseline arquitetural** para permitir comparações controladas e preservar o comportamento já testado.

Arquivos gerados no ambiente do projeto:

- `utils/avaliar_recuperacao.py`
- `benchmarks/resultados/recuperacao_v1.0_detalhes.csv`
- `benchmarks/resultados/recuperacao_v1.0_resumo.json`

## 5. Experimento com reranking

Foi avaliado o CrossEncoder multilíngue `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, em CPU, usando `sentence-transformers` 6.0.1 e `predict(..., batch_size=4)`. Compararam-se o RRF original 5+5, RRF ampliado 10+10 e RRF 10+10 seguido de reranking, sempre com saída final top 3.

| Configuração | Precision@3 | Recall@3 | Hit@3 | MRR@3 |
|---|---:|---:|---:|---:|
| RRF original 5+5 | 37,78% | 80,00% | 93,33% | 77,78% |
| RRF 10+10 | 37,78% | 72,22% | 80,00% | 73,33% |
| RRF 10+10 + reranker | 35,56% | 67,78% | 80,00% | 75,56% |

A latência média observada para o RRF 10+10 foi **0,780 s** e, com reranking, **4,107 s** (aproximadamente **5,3 vezes** maior). A primeira consulta apresentou aquecimento relevante (9,240 s), portanto os valores não devem ser tomados como benchmark rigoroso de latência nem comparados diretamente a uma latência não medida do baseline 5+5.

O reranker melhorou o Recall@3 em Q001 (33,33% → 100%) e Q006 (0% → 50%), mas piorou Q005 (50% → 0%), Q010 (100% → 0%), Q012 (100% → 50%) e Q013 (100% → 0%); nove perguntas permaneceram inalteradas. **Decisão:** não integrar o reranker, pois piorou as métricas agregadas e aumentou a latência.

Arquivos: `utils/avaliar_reranker.py`, `benchmarks/resultados/reranker_v1.0_detalhes.csv`, `benchmarks/resultados/reranker_v1.0_resumo.json`.

## 6. Estudo de caso Q006 — falha de recuperação, não de geração

**Pergunta original:** “Quem era o segundo maior artilheiro histórico do Flamengo?”
**Ground truth:** `chunk_1` e `chunk_10` (a resposta factual é **Dida, 264 gols**).

O RRF original recuperou `chunk_9`, `chunk_2`, `chunk_23`: dois trechos sobre Zico como maior artilheiro (508 gols) e um trecho sobre 2009, sem identificar o segundo colocado. A LLM **não inventou** Dida; informou que o contexto era insuficiente.

**Pergunta alternativa:** “Quem são os maiores artilheiros históricos do Flamengo?”
O RRF recuperou `chunk_11`, `chunk_1`, `chunk_0`, incluindo a lista histórica. A LLM respondeu: Zico (508), Dida (264), Henrique Frade (212), Pirilo (208) e Romário (204). Os testes mostram sensibilidade da recuperação à formulação da pergunta; não demonstram que o usuário sempre conseguirá resolver uma falha reformulando a consulta.

### 6.1 Posições do chunk_1

| Recuperador | Pergunta original | Pergunta alternativa |
|---|---:|---:|
| BM25 | 31º | 2º |
| Vetorial | 6º | 4º |
| RRF original 5+5 | Ausente da fusão | 2º |

Com BM25 top 5 + vetorial top 6, o `chunk_1` entrou na fusão, mas ficou em **9º** e continuou fora do contexto final. Ampliar candidatos, por si só, não garantiu a resposta.

### 6.2 Sensibilidade lexical

A tokenização original remove acentos, mas não reduz singular/plural. O documento usa `maiores`, `artilheiros`, `históricos` e uma lista numerada (`2. Dida`), enquanto a Q006 usa `maior`, `artilheiro`, `histórico` e `segundo`.

| Formulação testada | Posição BM25 do chunk_1 | Score BM25 |
|---|---:|---:|
| “Quem era o segundo maior artilheiro histórico do Flamengo?” | 31º | 2,3873 |
| “Quem era o segundo maior artilheiros históricos do Flamengo?” | 5º | 5,9816 |
| “Quem era o segundo maiores artilheiros históricos do Flamengo?” | 3º | 8,0541 |
| “Quem são os maiores artilheiros históricos do Flamengo?” | 2º | 10,6829 |

As formulações intermediárias são **artificiais**, usadas para isolar aspectos lexicais; a última também altera outras palavras. Não se deve atribuir toda a diferença exclusivamente ao plural.

## 7. Experimento com stemming português

O `SnowballStemmer("portuguese")`, do NLTK, aproximou `maior/maiores → maior`, `artilheiro/artilheiros → artilheir` e `histórico/históricos → histór`. O stemming foi aplicado às perguntas e aos documentos em **índice BM25 temporário em memória**, preservando o índice original.

Para a Q006, a posição lexical do `chunk_1` melhorou de **31º para 9º**, ainda fora do top 5. Para a pergunta alternativa, mudou de 2º para 3º. Os scores de índices com tokenização diferente não devem ser comparados como se estivessem na mesma escala.

### 7.1 Resultados agregados

| Método | Precision@3 | Recall@3 | Hit@3 | MRR@3 |
|---|---:|---:|---:|---:|
| BM25 original | 37,78% | 80,00% | 93,33% | 81,11% |
| BM25 stemming | 37,78% | 78,89% | 86,67% | 82,22% |
| RRF original | 37,78% | 80,00% | 93,33% | 77,78% |
| **RRF stemming** | **42,22%** | **85,56%** | **93,33%** | **76,67%** |

No **Recall@3 por pergunta** do RRF, duas melhoraram, treze ficaram inalteradas e nenhuma piorou:

- **Q001:** 33,33% → 66,67%; resultados originais `[6,9,3]`, stemming `[9,1,6]`, relevantes `[1,2,9]`.
- **Q011:** 50% → 100%; originais `[67,55,48]`, stemming `[67,54,48]`, relevantes `[54,67]`.
- **Q006:** permaneceu em 0%; originais `[9,2,23]`, stemming `[9,2,11]`, relevantes `[1,10]`.

Embora não haja regressões no Recall@3 por pergunta, o **MRR@3 agregado caiu** de 77,78% para 76,67%; portanto, não é correto afirmar ausência de regressões em todas as dimensões. A amostra pequena e a possível diferença entre perguntas do benchmark e perguntas frequentes de usuários exigem cautela.

Arquivo experimental: `utils/avaliar_stemming.py`. Resultado: `benchmarks/resultados/stemming_v1.0_detalhes.csv`.

## 8. Testes exploratórios de geração: Prompt A × Prompt B

A Q006 foi executada com os três chunks originais `[9,2,23]`, no modelo `openai/gpt-oss-20b`, temperatura 0,2:

| Variante | Comportamento observado | Latência da LLM |
|---|---|---:|
| Prompt A (atual) | Declarou insuficiência de contexto; não inventou segundo colocado | 0,931 s |
| Prompt B (instrução de resposta parcial) | Também declarou insuficiência; não acrescentou informação sobre Zico | 1,013 s |

As duas respostas foram **adequadas em fidelidade ao contexto**. Uma execução por variante não permite inferir diferença estável de latência ou superioridade de prompt. Não houve ganho claro que justificasse substituir o prompt atual.

A resposta à pergunta alternativa, com o `chunk_1` presente, identificou corretamente a lista de cinco artilheiros. Esses são **testes de caso**, não avaliação sistemática de factualidade, completude, faithfulness ou taxa de alucinação nas 15 perguntas.

## 9. Decisões arquiteturais

1. **Manter RRF 5+5 → 3 como baseline v1.0**, sem alterações na produção.
2. **Não incorporar reranker**: piora agregada e latência adicional significativa no experimento.
3. **Não incorporar stemming automaticamente**: melhorou Precision@3 e Recall@3 do RRF, mas não resolveu Q006, reduziu ligeiramente MRR@3 e ainda requer validação adicional.
4. **Não otimizar exclusivamente Q006**: perguntas sobre posições específicas, como o segundo ou terceiro artilheiro, são consideradas menos prováveis do que consultas sobre o maior ou os maiores artilheiros. Trata-se de uma **hipótese de uso**, não de frequência empiricamente medida.
5. **Manter Q006 no benchmark como teste de robustez**, mesmo sem tratá-la como prioridade de otimização.
6. **Priorizar resposta fundamentada e abstenção segura** quando a recuperação não oferece evidências suficientes; não forçar a LLM a completar lacunas com conhecimento externo.
7. **Evitar etapas adicionais sem ganho proporcional** em qualidade, latência e custo, considerando o ambiente computacional limitado e o objetivo de operação prática do bot.

## 10. Limitações e trabalhos futuros

- O benchmark contém **15 perguntas** e pode não refletir a distribuição real de perguntas dos usuários. Futuramente, separar perguntas **representativas** de **desafiadoras**, sem apagar os casos difíceis.
- Os rótulos do ground truth foram validados para o corpus atual; mudanças no corpus, chunking ou metadados exigem revalidação.
- Métricas de recuperação não comprovam a qualidade da resposta final. Falta um protocolo reproduzível para avaliar **correção factual, fidelidade às fontes, completude, abstenção apropriada e latência ponta a ponta**.
- A latência de reranking foi observada em execução experimental com efeito de aquecimento; falta medição padronizada de p50/p95 e custos por pergunta.
- Em futuros experimentos de ingestão, comparar Markdown atual com chunking por títulos, Markdown normalizado com o mesmo chunking e saída estruturada Docling/HybridChunker, preservando um corpus de referência e controles experimentais. **Não modificar a base v1.0 agora.**
- Não inferir superioridade estatística a partir de pequenas diferenças de macro-média em 15 perguntas.

## 11. Reprodutibilidade e arquivos

**Base e avaliação:**

```text
benchmarks/
  corpus/corpus_v1.0.jsonl
  benchmark_v1.0_factual_validado.jsonl
  resultados/
    recuperacao_v1.0_detalhes.csv
    recuperacao_v1.0_resumo.json
    reranker_v1.0_detalhes.csv
    reranker_v1.0_resumo.json
    stemming_v1.0_detalhes.csv
utils/
  avaliar_recuperacao.py
  avaliar_reranker.py
  avaliar_stemming.py
scripts/
  rag_core.py
```

Os caminhos acima são os caminhos **informados durante os experimentos** no repositório de homologação; esta documentação foi consolidada a partir dos códigos e saídas compartilhados na conversa, sem acesso direto ao repositório local para auditar arquivos ou reproduzir as execuções.

**Encerramento em 25/10/2026:** benchmark de recuperação e experimentos diagnósticos documentados. Próxima fase, em outra sessão: desenhar e executar o benchmark de **qualidade das respostas da LLM**, sem adicionar algoritmos ao pipeline antes de estabelecer uma medição adequada.
