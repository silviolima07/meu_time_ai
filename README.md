# ⚽ Meu Time IA

Assistente inteligente sobre futebol desenvolvido com **RAG (Retrieval-Augmented Generation)**, busca híbrida, Telegram e suporte a interação por **texto e voz**.

O projeto utiliza uma base de conhecimento própria sobre o Flamengo e combina recuperação lexical e semântica antes de enviar o contexto para uma LLM.

Além de responder por texto, o sistema permite receber perguntas em áudio, transcrevê-las e gerar respostas faladas.

---

## 🎯 Objetivo

O **Meu Time IA** foi criado como um projeto prático de AI Engineering para explorar a construção de uma aplicação completa baseada em IA generativa.

A proposta é permitir que o usuário faça perguntas sobre seu time e receba respostas fundamentadas em uma base de conhecimento própria.

A implementação atual utiliza o Flamengo como primeira base de conhecimento.

Entre os temas disponíveis estão:

- história do clube;
- fundação;
- títulos;
- jogadores;
- ídolos;
- competições;
- fatos históricos;
- informações presentes nos documentos utilizados pelo RAG.

O objetivo não é simplesmente enviar a pergunta diretamente para uma LLM.

Antes da geração da resposta, o sistema recupera os trechos mais relevantes da base de conhecimento.

---

# 🏗️ Arquitetura atual

O fluxo principal da aplicação é:

```text
                    ┌──────────────────────┐
                    │       Usuário        │
                    │      Telegram        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Pergunta        │
                    │    texto ou áudio    │
                    └──────────┬───────────┘
                               │
                 áudio         │        texto
                  ┌────────────┴────────────┐
                  ▼                         │
         ┌─────────────────┐                │
         │ Faster Whisper  │                │
         │ Speech-to-Text  │                │
         └────────┬────────┘                │
                  │                         │
                  └────────────┬────────────┘
                               ▼
                    ┌──────────────────────┐
                    │     RAG Híbrido      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
     ┌─────────────────┐              ┌─────────────────┐
     │      BM25       │              │ Busca Vetorial  │
     │ busca lexical   │              │    ChromaDB     │
     └────────┬────────┘              └────────┬────────┘
              │                                 │
              └────────────────┬────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │         RRF          │
                    │ Reciprocal Rank      │
                    │       Fusion         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Top-K documentos  │
                    │      relevantes      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Groq API        │
                    │         LLM          │
                    └──────────┬───────────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                     ▼                   ▼
              ┌─────────────┐    ┌─────────────┐
              │    Texto    │    │    Áudio    │
              │ detalhado   │    │ condensado  │
              └─────────────┘    └──────┬──────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │   Piper TTS     │
                               │ Text-to-Speech  │
                               └────────┬────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │     FFmpeg      │
                               │   OGG / Opus    │
                               └────────┬────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │    Telegram     │
                               └─────────────────┘

# 🔎 RAG com busca híbrida

A recuperação das informações combina duas estratégias diferentes.

## BM25 — busca lexical

O BM25 busca documentos considerando a ocorrência e a relevância das palavras presentes na pergunta.

Esse mecanismo é especialmente útil para:

- nomes;
- datas;
- títulos;
- jogadores;
- expressões específicas;
- termos que aparecem diretamente nos documentos.

---

## Busca vetorial — similaridade semântica

A segunda busca utiliza embeddings para localizar trechos semanticamente relacionados à pergunta.

O modelo utilizado é: **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2**.

Os vetores são armazenados no: **ChromaDB**.

Isso permite encontrar informações relacionadas ao significado da pergunta mesmo quando as mesmas palavras não aparecem literalmente no documento.

---

# 🔀 Reciprocal Rank Fusion — RRF

Os resultados das duas buscas são combinados por meio de **Reciprocal Rank Fusion**.

O RRF não depende diretamente dos scores produzidos pelos dois mecanismos.

Ele utiliza a posição que cada documento ocupa nos rankings.

De forma simplificada:

```text
BM25
1º chunk A
2º chunk C
3º chunk B

Busca vetorial
1º chunk B
2º chunk A
3º chunk D
```

O RRF combina os rankings e gera uma nova classificação.

Chunks que aparecem bem posicionados nas duas buscas tendem a receber maior relevância.

Isso permite aproveitar simultaneamente:

- precisão lexical do BM25;
- compreensão semântica dos embeddings.

Documentação detalhada:

[Busca híbrida BM25 + Vetorial + RRF](docs/busca_hibrida_bm25_vetorial_rrf.md)

---

# 🧠 Geração da resposta

Após o ranking final, os melhores chunks são utilizados para montar o contexto enviado à LLM.

O modelo é acessado através da: **Groq API**.

A LLM recebe:

```text
Pergunta do usuário
+
Contexto recuperado pelo RAG
+
Instruções de geração
```

O prompt determina que a resposta deve utilizar somente as informações recuperadas da base.

Caso o contexto não possua informações suficientes, o modelo é orientado a informar essa limitação em vez de inventar uma resposta.

---

# 💬 Integração com Telegram

A interface atual do projeto é um bot do Telegram.

O usuário pode:

- enviar perguntas por texto;
- enviar perguntas por áudio;
- receber respostas em texto;
- receber respostas em áudio.

Os principais comandos são:

```text
/start
/texto
/audio
```

O modo padrão é texto.

---

# 🎙️ Entrada por áudio

O usuário também pode enviar uma mensagem de voz.

A transcrição é realizada localmente com: **Faster Whisper**.

Configuração utilizada:

```text
Modelo: base
Device: CPU
Compute type: INT8
Idioma: português
```

O fluxo é:

```text
Áudio do Telegram
        ↓
Faster Whisper
        ↓
Texto transcrito
        ↓
RAG
        ↓
LLM
```

Depois disso a resposta segue o modo escolhido pelo usuário.

---

# 🔊 Respostas em áudio

O sistema utiliza atualmente: **Piper TTS**.

para transformar a resposta gerada pela LLM em voz.

O Piper gera inicialmente um arquivo: **WAV**.

Depois o FFmpeg converte o áudio para: **OGG / Opus**.

formato adequado para envio como mensagem de voz no Telegram.

---

# ⚡ Otimização do TTS

A primeira implementação utilizava **Kokoro TTS**.

Durante os testes foi identificado um grande gargalo de desempenho em CPU.

Foram observados tempos como:

```text
Kokoro/TTS: ~19 segundos
Kokoro/TTS: ~44 segundos
```

Em alguns testes, o tempo total chegou próximo de:

```text
48 segundos
```

para gerar uma resposta relativamente curta.

O ambiente utilizado não possui GPU e algumas otimizações do PyTorch não estavam disponíveis no processador.

Foi então testado o **Piper TTS**, baseado em ONNX.

No mesmo equipamento, uma resposta curta chegou a ser sintetizada em aproximadamente:

```text
2 segundos
```

Em outro teste:

```text
Duração do áudio: aproximadamente 1 minuto e 10 segundos
Tempo de síntese Piper: aproximadamente 15 segundos
```

A substituição reduziu significativamente a latência do modo de voz.

---

# 🎧 Respostas adaptadas ao canal

Outra otimização importante foi separar o comportamento da LLM conforme o tipo de resposta.

Uma resposta adequada para leitura nem sempre é adequada para áudio.

Por isso, o sistema informa à LLM se o usuário está no modo: **texto** ou **áudio**.

## Modo texto

A resposta pode apresentar mais detalhes e contexto.

## Modo áudio

A LLM recebe instruções para:

- preservar os fatos essenciais;
- eliminar repetições;
- reduzir detalhes secundários;
- utilizar frases naturais;
- evitar listas excessivamente longas;
- produzir preferencialmente respostas entre 20 e 40 segundos.

A resposta **não é truncada por caracteres**.

A própria LLM realiza uma condensação semântica do conteúdo.

Exemplo observado durante os testes:

```text
Resposta original:
mais de 1 minuto de áudio

Resposta adaptada:
aproximadamente 20 segundos
```

Isso reduz:

- tempo de geração do Piper;
- tamanho do arquivo;
- tempo de envio;
- tempo necessário para o usuário ouvir a resposta.

---

# ⏱️ Desempenho

A aplicação passou a registrar o tempo gasto nas principais etapas do pipeline.

Em testes realizados após as otimizações, respostas textuais apresentaram tempos próximos de 1 segundo.

Exemplos:

```text
0,73 s
1,06 s
0,97 s
```

Um teste de resposta em áudio apresentou:

| Etapa | Tempo |
|---|---:|
| RAG + LLM | 0,97 s |
| Piper TTS | 8,08 s |
| FFmpeg | 0,46 s |
| Envio Telegram | 2,52 s |

Essas medições foram importantes para identificar que o principal gargalo original não estava no RAG, mas no mecanismo de Text-to-Speech.

---

# 📚 Pipeline de preparação da base

A construção da base RAG foi dividida em etapas independentes.

```text
Documentos
    ↓
Carregamento
    ↓
Chunks
    ↓
Embeddings
    ↓
ChromaDB
    ↓
Índice BM25
    ↓
Busca híbrida
    ↓
RRF
    ↓
LLM
```

Os scripts foram organizados sequencialmente.

```text
scripts/
├── 00_configurar_estrutura.py
├── 01_carregar_documentos.py
├── 02_criar_chunks.py
├── 03_gerar_embeddings.py
├── 04_salvar_chroma.py
├── 05_criar_indice_bm25.py
├── 06_busca_hibrida.py
├── 07_perguntar_llm.py
├── 09_telegram_pipeline.py
└── rag_core.py
```

O arquivo: **rag_core.py**.

centraliza os principais componentes utilizados pelo pipeline atual.

---

# 📁 Estrutura do projeto

```text
meu_time_ai/
│
├── dados_processados/
│   ├── bm25/
│   ├── chunks/
│   ├── embeddings/
│   └── documentos.json
│
├── docs/
│   ├── 01-visao-inicial-meu-time-ai.md
│   ├── busca_hibrida_bm25_vetorial_rrf.md
│   └── ...
│
├── modelos/
│   └── piper/
│
├── scripts/
│   ├── 00_configurar_estrutura.py
│   ├── 01_carregar_documentos.py
│   ├── 02_criar_chunks.py
│   ├── 03_gerar_embeddings.py
│   ├── 04_salvar_chroma.py
│   ├── 05_criar_indice_bm25.py
│   ├── 06_busca_hibrida.py
│   ├── 07_perguntar_llm.py
│   ├── 09_telegram_pipeline.py
│   └── rag_core.py
│
├── chroma_db/
│
├── logs/
│
├── requirements.txt
├── env.example
└── README.md
```

---

# 🛠️ Tecnologias utilizadas

## Inteligência Artificial

- Retrieval-Augmented Generation — RAG
- Sentence Transformers
- Embeddings
- Groq API
- LLM

## Recuperação de informação

- BM25
- ChromaDB
- Busca vetorial
- Reciprocal Rank Fusion — RRF

## Voz

- Faster Whisper
- Piper TTS
- FFmpeg
- Opus

## Aplicação

- Python
- Telegram Bot API
- asyncio

---

# 🔐 Variáveis de ambiente

As credenciais utilizadas pela aplicação devem ser definidas no arquivo:

```text
.env
```

Exemplo:

```env
TELEGRAM_BOT_TOKEN=seu_token
GROQ_API_KEY=sua_chave
```

O arquivo real `.env` não deve ser versionado.

Utilize:

```text
env.example
```

como referência.

---

# ▶️ Executando o bot

Crie ou ative o ambiente virtual:

```bash
source .venv/bin/activate
```

Execute:

```bash
python3 scripts/09_telegram_pipeline.py
```

O bot ficará aguardando mensagens no Telegram.

---

# ⚙️ Execução como serviço

A aplicação pode ser configurada como um serviço Linux utilizando:

```text
systemd
```

Isso permite que o bot seja iniciado automaticamente após o reboot do servidor.

Para acompanhar os logs:

```bash
journalctl -u meu-time-ia -f
```

---

# 📊 Logs e auditoria

As interações do RAG são registradas para permitir análise posterior.

Entre as informações registradas estão:

- pergunta;
- resposta;
- chunks utilizados;
- ranking BM25;
- ranking vetorial;
- score RRF;
- fontes utilizadas.

Isso permite analisar por que determinada informação foi recuperada e utilizada pela LLM.

---

# 📖 Documentação técnica

O projeto possui documentos específicos descrevendo decisões e etapas da implementação.

### Busca híbrida

[BM25 + Busca Vetorial + RRF](docs/busca_hibrida_bm25_vetorial_rrf.md)

### Visão inicial do projeto

[Visão inicial do Meu Time IA](docs/01-visao-inicial-meu-time-ai.md)

A documentação continua sendo atualizada conforme novas funcionalidades são incorporadas.

---

# 🧪 Principais aprendizados

O projeto permitiu explorar na prática conceitos de:

- AI Engineering;
- RAG;
- chunking;
- embeddings;
- bancos vetoriais;
- busca lexical;
- busca semântica;
- rank fusion;
- redução de alucinações;
- integração com LLMs;
- Speech-to-Text;
- Text-to-Speech;
- modelos quantizados;
- inferência em CPU;
- ONNX;
- APIs;
- processamento assíncrono;
- bots;
- observabilidade;
- análise de latência;
- otimização de pipelines de IA.

---

# 🚀 Status atual

Atualmente o projeto possui:

- ✅ Base de conhecimento própria
- ✅ Geração de chunks
- ✅ Embeddings
- ✅ ChromaDB
- ✅ BM25
- ✅ Busca híbrida
- ✅ Reciprocal Rank Fusion
- ✅ Integração com Groq
- ✅ Bot Telegram
- ✅ Perguntas por texto
- ✅ Perguntas por áudio
- ✅ Transcrição com Whisper
- ✅ Respostas em texto
- ✅ Respostas em áudio
- ✅ Piper TTS
- ✅ Respostas adaptadas conforme a modalidade
- ✅ Registro de evidências do RAG
- ✅ Medição de desempenho
- ✅ Execução automática como serviço Linux

---

# 🔭 Próximas evoluções

Entre as possibilidades de expansão do projeto estão:

- inclusão de outros clubes;
- filtragem por metadado de time;
- expansão da base de conhecimento;
- avaliação automática do RAG;
- métricas de relevância da recuperação;
- análise de fidelidade da resposta ao contexto;
- cache de consultas;
- monitoramento de desempenho;
- comparação entre modelos de embedding e LLMs.

---

## Autor

**Silvio Lima**

Projeto desenvolvido como estudo prático de **AI Engineering, RAG e IA Generativa**.
