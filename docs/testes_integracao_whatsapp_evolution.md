# Testes de Integração --- WhatsApp Business + Evolution API

## 1. Objetivo

Este documento registra os testes realizados para validar a comunicação
entre um número do **WhatsApp Business**, conectado à **Evolution API**,
e um número pessoal de WhatsApp.

A ideia é manter um passo a passo reproduzível para que outra pessoa
consiga configurar e testar a integração posteriormente.

## 2. Ambiente utilizado

-   **Evolution API:** 2.3.7
-   **Evolution Manager:** `http://localhost:8080/manager`
-   **Instância:** `estudo`
-   **Execução da Evolution:** Docker
-   **Sistema cliente:** Windows
-   **Ferramenta de teste da API:** PowerShell
-   **WhatsApp Business:** número dedicado ao projeto
-   **WhatsApp pessoal:** utilizado como remetente/destinatário dos
    testes

> **Segurança:** não registre a API key real neste documento e não
> publique chaves no GitHub.

------------------------------------------------------------------------

## 3. Arquitetura básica validada

### Recebimento

``` text
WhatsApp pessoal
       ↓
WhatsApp Business
       ↓
Evolution API
```

### Envio

``` text
PowerShell / aplicação
       ↓
Evolution API
       ↓
WhatsApp Business
       ↓
WhatsApp pessoal
```

------------------------------------------------------------------------

## 4. Teste 1 --- Receber uma mensagem na Evolution

No WhatsApp pessoal, foi enviada uma mensagem para o número conectado ao
WhatsApp Business.

Mensagem utilizada:

``` text
boa tarde
```

Nos logs do container da Evolution apareceu o conteúdo da mensagem:

``` text
message: {
  conversation: 'boa tarde'
}
```

Também foram observados campos como:

``` text
pushName: 'Silvio Lima'
messageType: 'conversation'
```

### Resultado

A Evolution recebeu corretamente a mensagem enviada ao WhatsApp
Business.

**Status: APROVADO.**

``` text
WhatsApp pessoal
       ↓
WhatsApp Business
       ↓
Evolution API
       ✅
```

------------------------------------------------------------------------

## 5. Teste 2 --- Envio manual pelo WhatsApp Business

Foi enviada manualmente uma mensagem pelo aplicativo WhatsApp Business
para o WhatsApp pessoal.

Nos logs da Evolution apareceu:

``` text
"fromMe": true
```

Também foram registradas atualizações de status:

``` text
"status": 3
```

e posteriormente:

``` text
"status": 4
```

O campo `fromMe: true` indica que a mensagem foi originada pela própria
conta WhatsApp conectada à Evolution.

### Resultado

A Evolution acompanhou corretamente uma mensagem enviada manualmente
pelo WhatsApp Business.

**Status: APROVADO.**

------------------------------------------------------------------------

## 6. Teste 3 --- Verificar a Evolution API pelo PowerShell

Antes de realizar um envio pela API, foi verificado se a Evolution
estava acessível pela máquina local.

Abra o **PowerShell** e execute:

``` powershell
Invoke-RestMethod -Uri "http://localhost:8080"
```

A resposta obtida foi semelhante a:

``` text
status             : 200
message            : Welcome to the Evolution API, it is working!
version            : 2.3.7
clientName         : evolution_exchange
manager            : http://localhost:8080/manager
documentation      : https://doc.evolution-api.com
whatsappWebVersion : 2.3000.1047311227
```

O retorno:

``` text
status : 200
```

confirma que a Evolution API está funcionando e acessível localmente.

### Resultado

**Status: APROVADO.**

------------------------------------------------------------------------

## 7. Teste 4 --- Enviar mensagem pela Evolution API usando PowerShell

Este teste valida o envio de uma mensagem **sem utilizar manualmente o
aplicativo WhatsApp Business**.

Fluxo esperado:

``` text
PowerShell
   ↓
Evolution API
   ↓
Instância estudo
   ↓
WhatsApp Business
   ↓
WhatsApp pessoal
```

### 7.1 Obter a API key

No Evolution Manager, copie a API key utilizada pela
instalação/instância.

Não coloque a chave real neste arquivo.

### 7.2 Definir os headers

No PowerShell:

``` powershell
$headers = @{
    "apikey" = "SUA_API_KEY"
    "Content-Type" = "application/json"
}
```

Substitua `SUA_API_KEY` pela chave correta somente no ambiente de
execução.

### 7.3 Criar o corpo da mensagem

``` powershell
$body = @{
    number = "55DDDNUMERO"
    text   = "Teste enviado pelo Evolution API"
} | ConvertTo-Json
```

O telefone deve ser informado em formato internacional:

``` text
55 + DDD + número
```

Exemplo fictício:

``` text
5512999999999
```

Não utilize:

-   `+`
-   espaços
-   parênteses
-   hífens

### 7.4 Executar a chamada

``` powershell
Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8080/message/sendText/estudo" `
    -Headers $headers `
    -Body $body
```

O endpoint utilizado é:

``` text
POST /message/sendText/estudo
```

onde `estudo` é o nome da instância configurada na Evolution.

### 7.5 Retorno observado

A Evolution retornou um objeto semelhante a:

``` text
key              : @{remoteJid=55XXXXXXXXXXX@s.whatsapp.net; fromMe=True; id=...}
pushName         : Você
status           : PENDING
message          : @{conversation=Teste enviado pelo Evolution API}
messageType      : conversation
instanceId       : ...
source           : web
```

Os campos mais importantes para este teste foram:

``` text
fromMe=True
```

e:

``` text
conversation=Teste enviado pelo Evolution API
```

Isso confirmou que a mensagem foi criada pela conta conectada à
instância.

O primeiro retorno apresentou:

``` text
status : PENDING
```

Esse estado foi observado imediatamente após a API aceitar a
solicitação.

------------------------------------------------------------------------

## 8. Confirmação nos logs da Evolution

Depois do envio pelo PowerShell, os logs do container apresentaram novas
atualizações para a mesma mensagem.

Foi observado:

``` text
"fromMe": true
```

seguido por:

``` text
"status": 3
```

e posteriormente:

``` text
"status": 4
```

O mesmo ID da mensagem apareceu nas atualizações, permitindo acompanhar
o processamento da mensagem.

Além disso, a mensagem:

``` text
Teste enviado pelo Evolution API
```

chegou corretamente ao WhatsApp pessoal.

### Resultado

**Status: APROVADO.**

``` text
PowerShell
    ↓
Evolution API
    ↓
Instância estudo
    ↓
WhatsApp Business
    ↓
WhatsApp pessoal
    ✅
```

------------------------------------------------------------------------

## 9. Tentativa com Postman Web

Inicialmente foi tentado o envio utilizando o Postman no navegador:

``` text
POST http://localhost:8080/message/sendText/estudo
```

O Postman Web não conseguiu acessar o serviço local porque a requisição
estava sendo executada por um agente remoto/cloud.

O endereço:

``` text
localhost
```

refere-se à máquina onde a Evolution está sendo executada. Um agente
remoto não consegue acessar diretamente esse `localhost`.

Foi considerada a utilização do Postman Desktop/Desktop Agent. Como o
aplicativo instalado não abriu corretamente naquele momento, o teste foi
realizado diretamente pelo PowerShell.

Para uma Evolution executada localmente, o PowerShell mostrou-se uma
alternativa simples para validar a API.

------------------------------------------------------------------------

## 10. Resultado geral dos testes

Foram validadas as duas operações fundamentais da integração.

### Recebimento

``` text
WhatsApp pessoal
      ↓
WhatsApp Business
      ↓
Evolution API
      ✅
```

### Envio pela API

``` text
PowerShell / aplicação
      ↓
Evolution API
      ↓
WhatsApp Business
      ↓
WhatsApp pessoal
      ✅
```

Com isso, a camada básica de comunicação entre WhatsApp Business e
Evolution API está funcional.

------------------------------------------------------------------------

## 11. Próxima etapa --- Webhook

O próximo passo do projeto é retirar a necessidade de executar
manualmente o PowerShell.

A Evolution deverá informar automaticamente ao backend quando uma nova
mensagem chegar.

Arquitetura planejada:

``` text
Usuário
   ↓
WhatsApp
   ↓
Evolution API
   ↓
Webhook
   ↓
Backend Python
   ↓
Processamento
   ↓
Evolution API
   ↓
WhatsApp
   ↓
Usuário
```

O primeiro teste do webhook deverá utilizar uma resposta fixa.

Exemplo:

``` text
Usuário: oi
```

Resposta automática:

``` text
Olá! Sou o assistente Meu Time Aí.
```

Somente depois de validar esse fluxo será adicionada a camada de
inteligência, por exemplo:

``` text
WhatsApp
   ↓
Evolution
   ↓
Webhook
   ↓
Backend
   ↓
Agente / LLM / RAG
   ↓
Evolution
   ↓
WhatsApp
```

------------------------------------------------------------------------

## 12. Checklist de reprodução

-   [ ] Evolution API executando no Docker
-   [ ] Evolution Manager acessível
-   [ ] Instância criada
-   [ ] WhatsApp Business conectado à instância
-   [ ] Mensagem do WhatsApp pessoal recebida pela Evolution
-   [ ] `http://localhost:8080` respondendo com status 200
-   [ ] API key disponível
-   [ ] Número de destino no formato `55 + DDD + número`
-   [ ] POST para `/message/sendText/estudo` executado
-   [ ] Mensagem recebida no WhatsApp pessoal
-   [ ] Logs da Evolution confirmando o processamento
-   [ ] Próxima etapa: configurar webhook

------------------------------------------------------------------------

## Observação de segurança

Nunca salve no repositório:

-   API keys reais;
-   tokens;
-   senhas;
-   credenciais de serviços;
-   dados pessoais desnecessários.

Para exemplos e documentação, utilize valores fictícios ou variáveis de
ambiente.


##############################
PS F:\PROJETO_FUT\meu_time_ai> $headers = @{
>>     "apikey" = "estancia_id_api_key" # No .env ou no localhost:8080/manager
>>     "Content-Type" = "application/json"
>> }
PS F:\PROJETO_FUT\meu_time_ai> $body = @{
>>     number = "5512 numero pessoal"        
>>     text   = "Teste enviado pelo Evolution API"
>> } | ConvertTo-Json
PS F:\PROJETO_FUT\meu_time_ai> Invoke-RestMethod `
>>     -Method Post `
>>     -Uri "http://localhost:8080/message/sendText/estudo" `
>>     -Headers $headers `
>>     -Body $body