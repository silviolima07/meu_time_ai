# Otimização do Pipeline de Áudio

## Contexto

O Meu Time IA permite que o usuário escolha entre respostas em texto
ou áudio no Telegram.

Inicialmente, a síntese de voz era realizada com o Kokoro TTS.
Durante os testes em um notebook com processamento exclusivamente em CPU,
foi identificada uma latência elevada na geração das respostas em áudio.

## Problema identificado

As medições mostraram que o RAG e a LLM não eram os principais
responsáveis pela lentidão.

Exemplo de execução:

- RAG + LLM: aproximadamente 1 segundo
- Kokoro/TTS: entre 19 e 44 segundos
- FFmpeg: alguns segundos
- envio ao Telegram: alguns segundos

Na primeira utilização, o Kokoro ainda precisava carregar o modelo,
aumentando ainda mais o tempo de resposta.

Também foi observado o aviso:

Could not initialize NNPACK! Reason: Unsupported hardware.

O ambiente utilizado não possui GPU e o processador não suporta
algumas otimizações utilizadas pelo PyTorch.

## Substituição do Kokoro pelo Piper

Foi avaliado o Piper TTS como alternativa.

O Piper utiliza modelos ONNX e apresentou desempenho muito superior
no mesmo hardware.

### Resultado

Em um primeiro teste:

- Kokoro: aproximadamente 48 segundos
- Piper: aproximadamente 2 segundos

Em outro teste, uma resposta que produziu aproximadamente
1 minuto e 10 segundos de áudio foi sintetizada pelo Piper
em cerca de 15 segundos.

Com isso, o Piper passou a ser utilizado como mecanismo principal
de Text-to-Speech do projeto.

O fluxo passou a ser:

Pergunta
→ RAG
→ LLM
→ Piper TTS
→ WAV
→ FFmpeg / Opus
→ Telegram

## Adaptação da resposta ao canal

Outro problema identificado foi que respostas adequadas para leitura
nem sempre são adequadas para áudio.

Uma resposta textual detalhada poderia gerar mais de um minuto
de áudio, aumentando:

- tempo de síntese;
- tamanho do arquivo;
- tempo de envio;
- tempo que o usuário precisa ouvir.

Em vez de truncar a resposta após sua geração, o modo de resposta
passou a ser informado à LLM.

### Modo texto

No modo texto, a LLM pode fornecer uma resposta mais detalhada,
utilizando o nível de informação necessário para esclarecer
a pergunta.

### Modo áudio

No modo áudio, a LLM recebe instruções adicionais para:

- preservar os fatos essenciais;
- eliminar repetições;
- reduzir detalhes secundários;
- utilizar frases adequadas para fala;
- evitar listas excessivamente longas;
- produzir preferencialmente respostas entre 20 e 40 segundos.

A resposta não é cortada por quantidade de caracteres.
A própria LLM realiza uma síntese semântica do conteúdo.

## Arquitetura resultante

                  ┌──────────────┐
Pergunta ────────>│ RAG híbrido  │
                  └──────┬───────┘
                         │
                         ▼
                    ┌─────────┐
                    │   LLM   │
                    └────┬────┘
                         │
              ┌──────────┴──────────┐
              │                     │
          modo texto            modo áudio
              │                     │
              ▼                     ▼
      resposta detalhada     resposta condensada
                                    │
                                    ▼
                               Piper TTS
                                    │
                                    ▼
                                  WAV
                                    │
                                    ▼
                            FFmpeg / OGG Opus
                                    │
                                    ▼
                                Telegram

## Resultado observado

Após as otimizações:

### Texto

Respostas do RAG + LLM ficaram próximas de 1 segundo em vários testes.

Exemplos:

- 0,73 s
- 1,06 s
- 0,97 s

### Áudio

Em um dos testes:

- RAG + LLM: 0,97 s
- Piper/TTS: 8,08 s
- FFmpeg: 0,46 s
- envio ao Telegram: 2,52 s

Além disso, após a adaptação do prompt para o modo áudio,
uma resposta foi reduzida semanticamente para aproximadamente
20 segundos de fala, mantendo as informações principais.

## Conclusão

A otimização mostrou a importância de medir cada etapa do pipeline
antes de tentar melhorar o sistema.

Inicialmente, a percepção era de que o RAG estava lento.
As medições mostraram que o principal gargalo estava na síntese de voz.

A substituição do Kokoro pelo Piper reduziu significativamente
a latência de TTS em CPU.

A adaptação da geração da LLM conforme o canal de saída também
reduziu o tempo de síntese e melhorou a experiência do usuário,
sem simplesmente truncar as respostas.