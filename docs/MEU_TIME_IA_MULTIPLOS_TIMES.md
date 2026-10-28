# Meu Time IA — Implementação da Seleção de Múltiplos Times

**Data:** 28/10/2026
**Branch:** `feature/multiplos-times`
**Status:** Seleção e persistência implementadas e testadas.

## 1. Objetivo

Evoluir o Meu Time IA de uma aplicação dedicada ao Flamengo para uma arquitetura capaz de atender quatro clubes:

- Flamengo
- Santos
- Internacional
- Atlético Mineiro

Nesta primeira etapa, foram implementadas a seleção do clube pelo Telegram, a persistência da preferência no SQLite e a proteção contra consultas a bases ainda indisponíveis.

**Importante:** somente o Flamengo possui uma base RAG operacional nesta versão.

## 2. Arquitetura e fluxo do processo

![Fluxo de seleção de times, SQLite e RAG](imagens/fluxo_selecao_times.svg)

O processo funciona da seguinte maneira:

1. O usuário envia `/start` ou `/time`.
2. O Telegram apresenta quatro botões para seleção do clube.
3. O usuário seleciona seu time.
4. O `CallbackQueryHandler` executa a função `confirmar_time()`.
5. A função `salvar_time()` registra a preferência no SQLite.
6. O usuário envia uma pergunta em texto ou áudio.
7. O sistema recupera o `user_id` do Telegram.
8. A função `obter_time()` consulta a preferência armazenada.
9. O `time_id` é encaminhado para `processar_pergunta()`.
10. Se o clube for Flamengo, o RAG existente é executado.
11. Para os demais clubes, o sistema informa que a base ainda não está disponível, sem executar a recuperação RAG.

## 3. Arquivos envolvidos

| Arquivo | Responsabilidade |
|---|---|
| `scripts/09_telegram_pipeline.py` | Comandos, botões, callbacks e integração com o RAG |
| `scripts/preferencias_usuario.py` | Persistência das preferências no SQLite |
| `dados_processados/usuarios.sqlite3` | Banco de preferências dos usuários |
| `.gitignore` | Exclusão do banco SQLite do Git |
| `docs/imagens/fluxo_selecao_times.svg` | Diagrama visual da implementação |
| `docs/MEU_TIME_IA_MULTIPLOS_TIMES.md` | Documentação técnica |

## 4. Persistência SQLite

O módulo `preferencias_usuario.py` utiliza a biblioteca padrão `sqlite3` do Python.

A tabela possui dois campos:

- `user_id`: identificador único da conta do Telegram, utilizado como chave primária.
- `time_id`: identificador do clube escolhido.

A função `inicializar_banco()` cria a tabela quando necessário.

A função `salvar_time(user_id, time_id)` insere ou atualiza a preferência. O SQL utiliza `ON CONFLICT(user_id) DO UPDATE`, evitando registros duplicados.

A função `obter_time(user_id)` recupera o clube selecionado. Para usuários sem preferência cadastrada, retorna `flamengo`, mantendo a compatibilidade com a versão anterior.

O banco SQLite é independente do banco interno do ChromaDB e não é versionado no Git.

## 5. Implementação no Telegram

### 5.1 Seleção do clube

A função `selecionar_time()` apresenta os quatro clubes por meio de `InlineKeyboardButton` e `InlineKeyboardMarkup`.

Cada botão possui um identificador de callback, como `time:santos`.

### 5.2 Confirmação da escolha

A função `confirmar_time()`:

1. Recebe o clique do usuário.
2. Identifica e valida o clube selecionado.
3. Recupera o identificador do usuário.
4. Executa `salvar_time()`.
5. Confirma a seleção no Telegram.

O tratamento é registrado por `CallbackQueryHandler`, utilizando o padrão `^time:`.

### 5.3 Comandos disponíveis

| Comando | Finalidade |
|---|---|
| `/start` | Apresentar mensagem inicial e seleção de clube |
| `/time` | Selecionar ou alterar o clube |
| `/texto` | Configurar respostas em texto |
| `/audio` | Configurar respostas em áudio |
| `/ajuda` | Mostrar orientações e comandos |

## 6. Integração com o RAG

A função `processar_pergunta()` recebeu um novo parâmetro opcional:

`time_id: str = "flamengo"`

Esse valor padrão preserva a compatibilidade com as chamadas anteriores.

Os fluxos de texto e áudio consultam a preferência armazenada no SQLite e encaminham o clube selecionado ao processamento.

Para o Flamengo, permanece o pipeline existente:

- Recuperação lexical com BM25.
- Recuperação vetorial com ChromaDB.
- Fusão de resultados com RRF.
- Montagem do contexto.
- Geração da resposta por LLM via API.
- Envio da resposta ao Telegram.

Para Santos, Internacional e Atlético Mineiro, o processamento retorna uma mensagem de indisponibilidade da base, sem consultar o RAG do Flamengo.

## 7. Testes realizados

| Teste | Resultado |
|---|---|
| Verificação de sintaxe Python | Aprovado |
| Seleção do Santos | Funcionou |
| Pergunta com Santos selecionado | Base indisponível informada |
| Alteração para Flamengo | Funcionou |
| Pergunta sobre Santos com Flamengo selecionado | Informação não encontrada na base |
| Parada e inicialização do serviço | Preferência preservada |
| Reinicialização do serviço | Preferência preservada |

Os testes confirmaram o funcionamento da seleção, da recuperação da preferência e da persistência entre reinicializações.

## 8. Decisões técnicas

A implementação adotou as seguintes diretrizes:

- Utilizar SQLite em vez de introduzir um serviço adicional de banco de dados.
- Manter um único modelo de embeddings compartilhado.
- Preservar o pipeline existente do Flamengo.
- Não carregar modelos adicionais desnecessariamente.
- Manter os benchmarks como avaliações offline.
- Evitar alterações incompatíveis com as funções existentes.
- Considerar as limitações de memória do notebook utilizado como servidor.

## 9. Limitações atuais

Ainda não estão implementados:

- Bases documentais dos outros três clubes.
- Índices BM25 e coleções vetoriais independentes por clube.
- Roteamento da recuperação híbrida por `time_id`.
- Detecção explícita de perguntas sobre um clube diferente do selecionado.
- Orquestração com LangGraph.
- Benchmark multiclubes.

## 10. Próximas etapas

1. Organizar o corpus documental dos quatro clubes.
2. Definir a estrutura de armazenamento por clube.
3. Implementar índices independentes, compartilhando o modelo de embeddings.
4. Adaptar a busca híbrida para utilizar `time_id`.
5. Preservar a compatibilidade com o benchmark do Flamengo.
6. Implementar a detecção de conflitos entre a pergunta e o clube selecionado.
7. Avaliar a integração do LangGraph.
8. Executar benchmarks offline e documentar os resultados.

## 11. Conclusão

A primeira etapa da evolução para múltiplos times foi implementada e validada funcionalmente.

A seleção de clubes, a persistência SQLite e a proteção contra consultas a bases indisponíveis estão operacionais.

A próxima etapa será implementar o RAG multiclubes, com bases independentes e recuperação direcionada ao clube selecionado.
