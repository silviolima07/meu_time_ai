# Meu Time AI --- Documento Inicial do Projeto

**Versão:** 0.1\
**Data:** 01/09/2026\
**Status:** Concepção / preparação do ambiente

------------------------------------------------------------------------

## 1. Visão do projeto

O **Meu Time AI** é um assistente de futebol acessível pelo WhatsApp. A
proposta é permitir que qualquer torcedor converse naturalmente com um
assistente sobre seu time, sem precisar aprender comandos específicos ou
instalar um aplicativo próprio.

Exemplos de interação:

-   "Meu time é o Corinthians."
-   "Como está meu time no Brasileirão?"
-   "Quais foram os últimos cinco jogos?"
-   "Quando é o próximo jogo?"
-   "Quais são as últimas notícias?"
-   "Quem é o próximo adversário?"
-   "Compare meu time com o Palmeiras."
-   "Conte a história do clube."
-   "Quais são os principais títulos?"

O projeto será desenvolvido inicialmente como **laboratório e portfólio
de AI Engineering**, priorizando arquitetura em código, compreensão dos
componentes e evolução incremental.

------------------------------------------------------------------------

## 2. Objetivo

Construir um assistente capaz de:

1.  receber mensagens pelo WhatsApp;
2.  identificar o usuário pelo número de telefone;
3.  memorizar o time favorito do usuário;
4.  consultar dados atualizados de futebol;
5.  consultar notícias recentes;
6.  responder perguntas históricas utilizando uma base de conhecimento;
7.  manter contexto de conversa;
8.  selecionar automaticamente a fonte/ferramenta adequada;
9.  responder em linguagem natural;
10. futuramente receber e responder mensagens de áudio.

O diferencial não será apenas fornecer placares ou tabelas, mas oferecer
uma **experiência conversacional personalizada para o torcedor**.

------------------------------------------------------------------------

## 3. Público-alvo

Torcedores interessados em acompanhar clubes e competições do futebol
brasileiro por uma interface já conhecida: o WhatsApp.

O primeiro escopo será o **Campeonato Brasileiro Série A**, podendo
posteriormente ser ampliado para:

-   Copa do Brasil;
-   Libertadores;
-   Sul-Americana;
-   campeonatos estaduais;
-   Seleção Brasileira;
-   outras ligas.

------------------------------------------------------------------------

## 4. Arquitetura proposta

Arquitetura inicial:

``` text
Usuário
   │
   │ WhatsApp
   ▼
Número dedicado do projeto
   │
   ▼
WhatsApp Business
   │
   ▼
Evolution API
(Docker)
   │
   ▼
FastAPI
(Python)
   │
   ▼
Agente
   ├── API de futebol
   ├── PostgreSQL
   ├── LLM
   ├── Notícias / RSS / Web
   └── RAG
```

### Responsabilidade dos componentes

**WhatsApp Business**\
Interface utilizada pelo usuário.

**Evolution API**\
Ponte entre o WhatsApp e a aplicação. Será executada localmente em
Docker durante o desenvolvimento.

**FastAPI**\
Backend principal do projeto. Receberá os eventos da Evolution API e
será responsável por chamar os serviços da aplicação.

**Agente**\
Interpretará a intenção do usuário e decidirá qual ferramenta utilizar.

**API de futebol**\
Fornecerá informações estruturadas e atualizadas, como jogos,
classificação, calendário e estatísticas.

**PostgreSQL**\
Armazenará usuários, time favorito, preferências, histórico e outros
dados persistentes.

**RAG**\
Será utilizado para informações históricas e documentais sobre clubes,
competições e outros conteúdos que não dependem de atualização em tempo
real.

**LLM**\
Interpretará perguntas, selecionará ferramentas quando necessário e
transformará dados em respostas naturais.

------------------------------------------------------------------------

## 5. Princípio arquitetural

A lógica principal do sistema será implementada em **Python**, evitando
colocar as decisões centrais da aplicação em ferramentas de automação
visual.

O projeto não dependerá inicialmente do n8n.

``` text
Evolution API
      ↓
   FastAPI
      ↓
   Python
      ↓
Agent / Services
```

Ferramentas de automação poderão ser incorporadas futuramente apenas
quando houver uma necessidade clara, como integrações administrativas ou
tarefas periféricas.

------------------------------------------------------------------------

## 6. Estratégia de fontes

O agente não deverá utilizar o LLM como fonte factual para informações
que podem ser obtidas diretamente de fontes estruturadas.

### Dados dinâmicos

Exemplos:

-   classificação;
-   pontuação;
-   partidas;
-   resultados;
-   próximos jogos;
-   estatísticas;
-   escalações.

Fonte prevista: **API especializada em futebol**.

A primeira candidata para avaliação é a **API-Football**, cujo plano
gratuito atualmente oferece 100 requisições por dia. Antes da
implementação, serão testadas cobertura do Brasileirão, qualidade dos
dados e limitações do plano.

### Notícias

As notícias deverão vir de fontes atuais, por RSS, busca ou APIs
adequadas. O LLM deverá resumir ou organizar as informações, e não
inventá-las.

### Informações históricas

Exemplos:

-   fundação;
-   estádio;
-   grandes jogadores;
-   títulos;
-   história do clube;
-   momentos históricos.

Esses conteúdos poderão utilizar uma base documental própria e RAG.

**Observação:** letras integrais de hinos protegidos por direitos
autorais não deverão ser armazenadas/reproduzidas como funcionalidade do
assistente. Poderão ser apresentados dados históricos, autores e
contexto.

------------------------------------------------------------------------

## 7. Memória e personalização

Um objetivo importante será evitar que o usuário precise repetir
informações.

Exemplo:

``` text
Usuário: Meu time é o Santos.

Sistema:
telefone = 55...
time_favorito = Santos
```

Depois:

``` text
Usuário: Quando é o próximo jogo?
```

O sistema consulta o cadastro pelo telefone e entende que a pergunta se
refere ao Santos.

Estrutura conceitual inicial:

``` text
usuarios
--------
id
telefone
nome
time_favorito
data_criacao
```

A modelagem será detalhada posteriormente.

------------------------------------------------------------------------

## 8. Evolução planejada

### Fase 0 --- Preparação

-   adquirir número dedicado;
-   ativar o chip;
-   instalar/configurar WhatsApp Business;
-   preparar diretório e documentação;
-   verificar Docker;
-   criar repositório Git.

### Fase 1 --- WhatsApp + Evolution API

Objetivo: provar a comunicação.

``` text
WhatsApp → Evolution → aplicação
aplicação → Evolution → WhatsApp
```

Critério de sucesso: enviar uma mensagem ao número do projeto e receber
uma resposta simples gerada pela aplicação.

### Fase 2 --- Backend FastAPI

Criar backend Python independente da Evolution.

Primeiros endpoints:

``` text
GET  /health
POST /webhook/whatsapp
```

Critério de sucesso: receber corretamente mensagens enviadas pelo
WhatsApp.

### Fase 3 --- API de futebol

Integrar uma API esportiva.

Primeiras funcionalidades:

-   localizar clube;
-   obter classificação;
-   últimos jogos;
-   próximo jogo.

Critério de sucesso:

``` text
Usuário: Como está o Palmeiras?

Assistente:
posição
pontos
último jogo
próximo jogo
```

### Fase 4 --- Persistência

Adicionar PostgreSQL.

Primeira memória:

``` text
telefone → time favorito
```

Critério de sucesso:

``` text
Usuário: Meu time é o São Paulo.
Usuário: Qual é o próximo jogo?
```

O sistema deverá entender automaticamente o clube.

### Fase 5 --- Agente

O sistema passa a selecionar ferramentas conforme a intenção.

``` text
Pergunta
   ↓
Agente
   ├── futebol_api
   ├── noticias
   ├── rag
   └── banco
```

### Fase 6 --- Notícias

Adicionar busca de notícias recentes e fontes.

Exemplo:

``` text
Usuário: Quais são as notícias do meu time hoje?
```

### Fase 7 --- RAG

Criar base histórica dos clubes.

Exemplos:

-   história;
-   títulos;
-   estádios;
-   personagens;
-   confrontos históricos.

### Fase 8 --- Áudio

Fluxo previsto:

``` text
WhatsApp
   ↓
áudio
   ↓
Evolution
   ↓
Speech-to-Text
   ↓
Agente
   ↓
resposta
```

### Fase 9 --- Escalabilidade e observabilidade

Somente quando houver necessidade real:

-   Redis;
-   filas/workers;
-   cache;
-   Prometheus;
-   Grafana;
-   métricas de LLM;
-   métricas de RAG;
-   logs estruturados;
-   testes de carga.

------------------------------------------------------------------------

## 9. Primeiro passo físico --- adquirir o chip

O Galaxy M14 utilizado no projeto não possui eSIM, portanto será
utilizado **chip físico** em um segundo slot.

### Linha escolhida inicialmente

**Claro Pré-pago**

Motivos:

-   número brasileiro real;
-   não exige contratação de plano pós-pago;
-   adequado para manter uma conta dedicada do WhatsApp;
-   chip físico compatível com o aparelho;
-   possibilidade de manter a linha por recargas periódicas.

### Procedimento inicial

1.  Comprar um chip físico Claro Pré.
2.  Inserir no segundo slot do Galaxy M14.
3.  Ligar o aparelho.
4.  Aguardar a ativação da linha.
5.  Seguir o cadastro recebido por SMS ou utilizar os canais de ativação
    da Claro.
6.  Realizar identificação do titular.
7.  Fazer a primeira recarga.
8.  Confirmar e registrar o novo número.
9.  Instalar/configurar o WhatsApp Business.
10. Registrar o WhatsApp Business utilizando exclusivamente o novo
    número.

A documentação atual da Claro informa que, após inserir o chip e ligar o
aparelho, o usuário recebe por SMS o número da linha e as orientações
para cadastro. O processo pode exigir CPF, identificação digital e
selfie/documento.

------------------------------------------------------------------------

## 10. Separação dos números

A configuração pretendida será:

``` text
Galaxy M14

SIM 1
└── número pessoal
    └── WhatsApp pessoal

SIM 2
└── Claro Pré
    └── WhatsApp Business
        └── número exclusivo do projeto
```

O número do projeto não deverá ser utilizado como número pessoal.

Isso facilitará testes, demonstrações e eventual evolução do sistema.

------------------------------------------------------------------------

## 11. Evolution API

Após o número e o WhatsApp Business estarem funcionando, será
configurada a Evolution API.

Ambiente previsto:

``` text
Docker Compose
├── Evolution API
├── PostgreSQL
└── Redis
```

A versão atual da Evolution API utiliza Docker e sua configuração
oficial contempla PostgreSQL e Redis. O repositório oficial
disponibiliza arquivo `docker-compose`.

A Evolution será vinculada ao WhatsApp do novo número por meio do
mecanismo de dispositivo conectado/QR Code.

**Importante:** no modo baseado em WhatsApp Web/Baileys, a Evolution API
não é a API oficial da Meta. Isso é aceitável para o laboratório e
estudo inicial, mas deverá ser reavaliado caso o projeto se transforme
em serviço comercial.

------------------------------------------------------------------------

## 12. Estrutura inicial sugerida do diretório

``` text
meu-time-ai/
│
├── README.md
├── docs/
│   ├── 01-visao-inicial.md
│   ├── 02-arquitetura.md
│   ├── 03-evolution-api.md
│   ├── 04-api-futebol.md
│   └── decisoes/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── infrastructure/
│   ├── docker-compose.yml
│   └── .env.example
│
├── data/
│   ├── raw/
│   └── processed/
│
├── scripts/
│
├── .gitignore
└── LICENSE
```

**Nunca versionar `.env`, tokens, senhas, API keys ou credenciais do
WhatsApp.**

------------------------------------------------------------------------

## 13. Primeira lista de tarefas

-   [ ] Criar diretório `meu-time-ai`
-   [ ] Salvar este documento em `docs/01-visao-inicial.md`
-   [ ] Comprar chip físico Claro Pré
-   [ ] Inserir chip no SIM 2 do Galaxy M14
-   [ ] Ativar e cadastrar a linha
-   [ ] Fazer primeira recarga
-   [ ] Registrar o novo número na documentação privada do projeto
-   [ ] Configurar WhatsApp Business
-   [ ] Testar envio e recebimento normal de mensagens
-   [ ] Verificar instalação do Docker/Docker Compose no computador
-   [ ] Criar repositório Git local
-   [ ] Criar `.gitignore`
-   [ ] Criar `.env.example`
-   [ ] Subir Evolution API
-   [ ] Vincular Evolution ao WhatsApp Business
-   [ ] Testar envio de mensagem pela Evolution
-   [ ] Criar primeiro backend FastAPI
-   [ ] Testar webhook WhatsApp → FastAPI
-   [ ] Avaliar API-Football com dados reais do Brasileirão

------------------------------------------------------------------------

## 14. Critério do primeiro marco

O **Marco 1** estará concluído quando for possível:

1.  enviar uma mensagem de outro telefone para o número dedicado;
2.  a Evolution API receber essa mensagem;
3.  o FastAPI processá-la;
4.  uma resposta ser produzida localmente;
5.  a Evolution enviar a resposta;
6.  o usuário recebê-la no WhatsApp.

Inicialmente a resposta poderá ser fixa:

``` text
Usuário:
Olá

Assistente:
Olá! O assistente Meu Time AI está funcionando.
```

Nesse ponto teremos validado toda a infraestrutura básica antes de
adicionar LLM, agente, RAG ou API esportiva.

------------------------------------------------------------------------

## 15. Princípios do desenvolvimento

1.  **Começar simples.** Não adicionar componentes antes de existir uma
    necessidade.
2.  **Lógica principal em código.** Python/FastAPI será o núcleo da
    aplicação.
3.  **Dados antes do LLM.** Informações factuais atualizadas devem vir
    de APIs/fontes confiáveis.
4.  **LLM como inteligência, não banco de dados.**
5.  **Componentes desacoplados.** Evolution, backend, LLM, banco e
    fontes externas devem poder evoluir separadamente.
6.  **Testabilidade.** Regras e ferramentas devem ser testáveis sem
    depender do WhatsApp.
7.  **Observabilidade progressiva.** Métricas serão adicionadas conforme
    o sistema crescer.
8.  **Segredos fora do Git.**
9.  **Documentar decisões.** Mudanças arquiteturais importantes devem
    registrar problema, alternativas e decisão.
10. **Construir como produto.** A experiência do torcedor é tão
    importante quanto a tecnologia.

------------------------------------------------------------------------

## 16. Referências iniciais

-   Claro --- ativação do chip Pré:
    https://www.claro.com.br/celular/planos-pre/como-ativar-seu-chip
-   Evolution API --- repositório oficial:
    https://github.com/evolution-foundation/evolution-api
-   Evolution API --- Docker Compose oficial:
    https://github.com/evolution-foundation/evolution-api/blob/main/docker-compose.yaml
-   API-Football: https://www.api-football.com/

------------------------------------------------------------------------

## 17. Próxima ação

**Ação imediata:** adquirir o chip físico Claro Pré e ativar o novo
número.

Enquanto isso, o diretório e o repositório do projeto podem ser
preparados, mas a implementação deve seguir incrementalmente. O primeiro
objetivo técnico será estabelecer a comunicação:

``` text
WhatsApp → Evolution API → FastAPI → Evolution API → WhatsApp
```

Somente depois dessa etapa estar estável serão adicionados LLM, API de
futebol, memória, notícias e RAG.
