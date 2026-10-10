# Meu Time IA — Documentação de infraestrutura e implantação

**Data de referência:** 10/10/2026  
**Ambiente documentado:** homologação, com referências à produção existente  
**Estado:** integração Telegram → RAG validada; API e Tunnel executados por `systemd`

> Este documento registra as configurações e os testes relatados durante a implantação. Dados não confirmados, especialmente os nomes exatos dos servidores DNS, estão explicitamente sinalizados para conferência. Não armazenar tokens, senhas nem segredos neste documento ou no repositório.

## 1. Objetivo

Disponibilizar o assistente **Meu Time IA** por Telegram, com processamento RAG no notebook Ubuntu, entrada pública protegida por Cloudflare e gerenciamento dos processos de infraestrutura via `systemd`. A homologação é isolada do bot de produção existente.

## 2. Visão geral da arquitetura

```text
Usuário (Telegram)
       |
       v
Telegram Bot API / webhook
       |
       v
Cloudflare Worker: meu-time-ia-gateway
  - valida X-Telegram-Bot-Api-Secret-Token
  - extrai a pergunta da mensagem
  - envia POST /perguntar com X-Backend-API-Key
       |
       v
https://api.silviolima.dev.br
       |
       v
Cloudflare Tunnel (cloudflared no Ubuntu)
       |
       v
http://127.0.0.1:8001
       |
       v
api_homolog.py
  - valida BACKEND_API_KEY
  - busca_hibrida(): BM25 + ChromaDB + RRF
  - montar_contexto(): trechos e origens
  - perguntar_llm(): chamada à API Groq
       |
       v
Resposta JSON -> Worker -> Telegram sendMessage
```

**Observação:** o Worker responde rapidamente `200 OK` ao webhook e usa `ctx.waitUntil()` para continuar o processamento. Isso reduz bloqueios no webhook, mas não substitui um mecanismo durável de filas, nem garante ausência de mensagens duplicadas.

## 3. Domínio e DNS — `silviolima.dev.br`

O domínio **`silviolima.dev.br`** foi configurado para utilizar o **Cloudflare como provedor de DNS autoritativo**, mediante alteração dos servidores DNS no painel do **Registro.br**, conforme captura fornecida do painel de configuração.

- **Domínio:** `silviolima.dev.br`
- **Gerenciamento DNS:** Cloudflare
- **Subdomínio da API:** `api.silviolima.dev.br`
- **URL pública da API:** `https://api.silviolima.dev.br`
- **Rota interna de origem:** `http://127.0.0.1:8001` no Ubuntu, alcançada via Tunnel
- **Nameserver Cloudflare 1:** `noor.ns.cloudflare.com`
- **Nameserver Cloudflare 2:** `wells.ns.cloudflare.com`
- **Registrador:** Registro.br. **Delegação de nameservers:** confirmada na captura fornecida do painel do Registro.br. **Registros DNS específicos:** conferir no painel Cloudflare.

### 3.1 O que significa a mudança dos nameservers

A delegação do DNS do domínio passa a apontar para os servidores autoritativos atribuídos pelo Cloudflare. A partir daí, os registros DNS são administrados no Cloudflare, enquanto a propriedade e a renovação do domínio continuam sob responsabilidade do registrador, salvo transferência formal de registro.

**Não confundir:** nameservers (`*.ns.cloudflare.com`) não são URLs de aplicação nem servidores de hospedagem. Os dois valores exatos foram informados a partir da captura do painel do Registro.br.

### 3.2 Subdomínio da API

O endereço `api.silviolima.dev.br` foi testado externamente com sucesso. O Cloudflare encaminha as requisições ao Tunnel, que alcança o serviço local na porta `8001`. O registro DNS específico criado para essa rota (por exemplo, o alvo de um CNAME de Tunnel) deve ser confirmado no painel Cloudflare, em vez de presumido.

## 4. Cloudflare Worker — gateway Telegram

**Nome do Worker:** `meu-time-ia-gateway`  
**Endpoint Workers:** `https://meu-time-ia-gateway.silviolima07.workers.dev`  
**Finalidade:** receber atualizações do webhook Telegram, autenticar a origem, consultar a API de homologação e enviar a resposta ao chat.

### 4.1 Variáveis e segredos

| Nome | Tipo no Cloudflare | Finalidade |
|---|---|---|
| `BACKEND_URL` | Variable | `https://api.silviolima.dev.br` |
| `BACKEND_API_KEY` | Secret | Autenticação Worker → API Python |
| `WEBHOOK_SECRET` | Secret | Validação da chamada Telegram → Worker |
| `TELEGRAM_BOT_TOKEN` | Secret | Chamada à Telegram Bot API |

**Segurança:** não expor os valores dos segredos em código, prints, documentação, Git ou logs.

### 4.2 Comportamento implementado

1. Requisições que não são `POST` recebem mensagem simples de gateway ativo.
2. Requisições `POST` têm o cabeçalho `X-Telegram-Bot-Api-Secret-Token` comparado ao `WEBHOOK_SECRET`.
3. O Worker extrai `update.message.chat.id` e `update.message.text`.
4. Chama `POST ${BACKEND_URL}/perguntar`, enviando `{ "pergunta": "...", "modo": "texto" }` e o cabeçalho `X-Backend-API-Key`.
5. Lê o campo `resposta` do JSON retornado e envia ao Telegram por `sendMessage`.
6. Em falha de backend, envia uma mensagem de indisponibilidade.
7. O processamento usa `ctx.waitUntil()` após devolver `200 OK` ao webhook.

**Limitações atuais:** somente perguntas em texto; os comandos `/texto` e `/audio`, geração de áudio com Piper TTS, deduplicação de atualizações e processamento assíncrono durável ainda precisam de implementação ou validação nessa nova arquitetura.

## 5. Cloudflare Tunnel — Ubuntu

O Tunnel foi instalado como serviço do sistema e já estava ativo antes da configuração da API via `systemd`.

**Serviço:** `cloudflared.service`  
**Executável observado:** `/usr/bin/cloudflared`  
**Comando observado:**

```bash
/usr/bin/cloudflared --no-autoupdate tunnel run --token-file /etc/cloudflared/token
```

**Estado observado:** `enabled` e `active (running)`.

O token do Tunnel está em `/etc/cloudflared/token` e **não deve ser copiado para documentação nem repositórios**.

### Diagnóstico realizado

Um teste inicial retornou `HTTP/2 502` em `https://api.silviolima.dev.br/health`. O teste local `curl http://127.0.0.1:8001/health` retornou `Connection refused`: não havia API escutando na porta `8001`. Após iniciar a API, os testes locais e públicos retornaram HTTP 200. Portanto, o erro 502 daquele momento foi explicado pela indisponibilidade do serviço de origem, não por uma falha permanente no DNS.

## 6. API Python de homologação

**Diretório:** `/home/silvio/projetos/meu_time_ai_homolog`  
**Arquivo:** `api_homolog.py`  
**Python virtualenv:** `/home/silvio/projetos/meu_time_ai_homolog/.venv/bin/python`  
**Python base:** `/usr/bin/python3.10`  
**Escuta:** `127.0.0.1:8001`  
**Servidor HTTP:** `ThreadingHTTPServer`

### 6.1 Endpoints

| Método | Endpoint | Autenticação | Resposta |
|---|---|---|---|
| `GET` | `/health` | Não exigida | `{"status":"online","servico":"Meu Time IA - Homologacao"}` |
| `POST` | `/perguntar` | `X-Backend-API-Key` | `{"resposta":"...","fontes_recuperadas":N}` |

O endpoint `/perguntar` valida o cabeçalho com comparação segura (`hmac.compare_digest`), valida JSON, tamanho da requisição, pergunta e modo (`texto` ou `audio`). O fato de aceitar `modo=audio` não significa que a resposta já seja sintetizada em voz nessa API: a implementação atual retorna texto JSON.

### 6.2 Configuração da chave

A chave é lida de `.env.api`, no diretório de homologação:

```dotenv
BACKEND_API_KEY=<valor-secreto>
```

- Arquivo protegido com `chmod 600 .env.api`.
- Arquivo deve constar do `.gitignore`.
- O valor deve ser idêntico ao Secret `BACKEND_API_KEY` do Worker.
- Alterações nesse arquivo exigem reinicialização da API, pois a chave é carregada na inicialização.

Durante a implantação, houve uma configuração inicial incorreta contendo o texto de exemplo `SUA_CHAVE_GERADA`. Após corrigir o valor e reiniciar a API, a autenticação passou a funcionar. Não reproduzir o segredo real em logs ou documentação.

## 7. Pipeline RAG

**Módulo:** `scripts/rag_core.py`.

```text
Pergunta
  -> busca_bm25()
  -> busca_vetorial() [ChromaDB + embeddings]
  -> reciprocal_rank_fusion() [RRF]
  -> busca_hibrida() [ranking final]
  -> montar_contexto() [arquivo, categoria, texto]
  -> perguntar_llm() [Groq]
  -> resposta em texto
```

**Verificações observadas:**

- Índice BM25 carregado.
- ChromaDB carregado com **72 registros**.
- Modelo de embeddings carregado.
- Pergunta de teste **“Quem foi Zico?”** respondida corretamente pelo RAG.
- Pergunta **“Quantos filhos tem Zico?”** recebeu resposta de ausência de informação no contexto. Isso é consistente com a instrução de não inventar fatos, mas ainda não prova se a informação está ausente do corpus ou se não foi recuperada.

### Avaliação futura

Planeja-se registrar, por consulta, pergunta, identificador, rankings BM25/vetorial, scores, resultado RRF, chunks selecionados, arquivos e metadados de origem, contexto enviado, modelo, resposta, tempos e erros. Preferência inicial: logs estruturados JSONL, sem armazenar segredos. **Ainda não implementado como rastreabilidade completa.**

## 8. Serviços systemd

### 8.1 Produção — serviço existente

**Serviço:** `meu-time-ia.service`  
**Estado observado:** `enabled`, `active (running)`  
**WorkingDirectory:** `/home/silvio/projetos/meu_time_ai`  
**ExecStart:**

```text
/home/silvio/projetos/meu_time_ai/.venv/bin/python -u /home/silvio/projetos/meu_time_ai/scripts/09_telegram_pipeline.py
```

Este é o bot anterior de produção e **não foi alterado** durante a configuração da API de homologação. O serviço executa um processo Python próprio; seu papel deve permanecer separado da nova integração por webhook.

### 8.2 Tunnel — serviço existente

**Serviço:** `cloudflared.service`  
**Estado observado:** `enabled`, `active (running)`.

### 8.3 API de homologação — serviço criado

**Serviço:** `meu-time-api-homolog.service`  
**Arquivo:** `/etc/systemd/system/meu-time-api-homolog.service`

```ini
[Unit]
Description=Meu Time IA - API de Homologacao
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=silvio
WorkingDirectory=/home/silvio/projetos/meu_time_ai_homolog
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/silvio/projetos/meu_time_ai_homolog/.venv/bin/python -u /home/silvio/projetos/meu_time_ai_homolog/api_homolog.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Validação observada em 10/10/2026:**

- `Loaded: ... enabled`
- `Active: active (running)`
- Processo Python iniciado via `.venv`.
- BM25, ChromaDB (72 registros) e modelo de embeddings carregados.
- `GET /health` respondeu `200` nos logs.
- Memória observada para o serviço: aproximadamente **1,0 GB** no momento da medição.

### Comandos operacionais

```bash
# Estado da API de homologação
systemctl status meu-time-api-homolog.service --no-pager

# Logs em tempo real (Ctrl+C apenas encerra a visualização)
journalctl -u meu-time-api-homolog.service -f

# Reiniciar a API após mudanças de código/configuração
sudo systemctl restart meu-time-api-homolog.service

# Estado do Tunnel
systemctl status cloudflared.service --no-pager

# Estado do bot anterior de produção
systemctl status meu-time-ia.service --no-pager

# Teste local
curl -i --max-time 10 http://127.0.0.1:8001/health

# Teste externo
curl -i --max-time 10 https://api.silviolima.dev.br/health
```

**Cuidado:** não iniciar manualmente `python api_homolog.py` enquanto o serviço `meu-time-api-homolog.service` estiver ativo, pois ambos tentariam ocupar a porta `8001`.

## 9. Testes de ponta a ponta concluídos

| Teste | Resultado relatado |
|---|---|
| `GET /health` local | HTTP 200 após iniciar a API |
| `GET /health` público via Cloudflare | HTTP 200 |
| `POST /perguntar` local, autenticado | HTTP 200; resposta RAG |
| `POST /perguntar` público, autenticado | HTTP/2 200 |
| Deploy do Worker | Sem erro relatado |
| Pergunta ao bot de homologação no Telegram | Resposta rápida recebida |
| Pergunta fora do contexto disponível | Resposta de insuficiência de informação |
| API sob `systemd` | Serviço ativo, habilitado, `/health` 200 |

## 10. Pendências e próximos passos

1. **Conferir os registros DNS específicos do domínio/subdomínio** no painel Cloudflare. Os dois nameservers já estão documentados a partir do Registro.br.
2. **Validar a separação de bots e webhooks** entre produção e homologação, especialmente para evitar consumo concorrente de atualizações do mesmo bot.
3. **Implementar `/texto` e `/audio`** no fluxo novo, incluindo integração com Piper TTS e armazenamento da preferência de resposta.
4. **Deduplicação e robustez:** tratar reentregas do webhook, indisponibilidade do backend, limites de tempo, filas e reprocessamento.
5. **Observabilidade do RAG:** logs estruturados de pergunta, recuperação, RRF, trechos, fontes, resposta e latência.
6. **Segurança:** rotação periódica de segredos, política de acesso ao backend, limitação de requisições e revisão dos logs para não vazar dados sensíveis.
7. **Operação:** verificar comportamento após reinicialização real do Ubuntu e acompanhar memória no notebook de 8 GB, pois produção e homologação coexistem.
8. **Documentação do repositório:** integrar este arquivo em `docs/` e criar um link no `README.md`.

## 11. Resumo do estado atual

A infraestrutura de homologação está operacional: o Telegram recebe respostas do RAG por meio do Cloudflare Worker e Tunnel, com API Python autenticada no Ubuntu. O Tunnel e a API são gerenciados pelo `systemd`, e o serviço de produção existente permanece separado. A infraestrutura básica foi testada com sucesso; recursos de áudio, rastreabilidade detalhada e garantias adicionais de confiabilidade permanecem como evoluções futuras.
