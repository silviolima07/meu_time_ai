# Flamengo — Imagens e referências visuais

> Este arquivo organiza o uso de imagens no projeto Meu Time IA.
> As imagens não devem ser tratadas como fatos textuais sem metadados associados.

## Estrutura recomendada

```text
flamengo/
└── imagens/
    ├── escudo/
    ├── estadio/
    ├── torcida/
    ├── historia/
    ├── jogadores/
    └── titulos/
```

## Tipos de imagem

### Escudo
Uso:
- identificação do clube;
- interface;
- respostas institucionais.

Metadados sugeridos:
- categoria: escudo
- clube: Flamengo
- descrição: Escudo do Clube de Regatas do Flamengo
- fonte
- direitos/licença

### Maracanã
Uso:
- perguntas sobre estádio;
- jogos históricos;
- finais e grandes públicos.

Metadados sugeridos:
- categoria: estadio
- nome: Maracanã
- cidade: Rio de Janeiro
- relação: estádio associado a grandes jogos do Flamengo

### Torcida
Uso:
- perguntas sobre a Nação Rubro-Negra;
- conteúdo visual de apoio.

Metadados sugeridos:
- categoria: torcida
- clube: Flamengo
- evento
- data aproximada
- fonte
- direitos/licença

### Zico
Uso:
- história;
- maior artilheiro;
- geração de 1981.

Metadados sugeridos:
- categoria: jogador_historico
- nome: Zico
- período: 1971–1983 e 1985–1989
- descrição
- fonte
- direitos/licença

### Libertadores de 1981
Uso:
- primeira Libertadores;
- geração de Zico;
- caminho para o Mundial de 1981.

### Mundial de 1981
Uso:
- conquista mundial;
- vitória sobre o Liverpool.

### Libertadores recentes
Pastas sugeridas:
- libertadores_2019
- libertadores_2022
- libertadores_2025

### Elenco atual
Pasta:
- jogadores/2026/

Como o elenco muda, as imagens devem ter:
- nome do jogador;
- temporada;
- data da foto;
- fonte.

## Arquivo de metadados recomendado

Além das imagens, mantenha um arquivo CSV ou JSON.

Exemplo em JSON:

```json
{
  "arquivo": "zico_1981.jpg",
  "categoria": "jogador_historico",
  "nome": "Zico",
  "clube": "Flamengo",
  "temporada": "1981",
  "descricao": "Zico durante a geração campeã da Libertadores e do Mundial de 1981",
  "fonte": "preencher",
  "licenca": "preencher"
}
```

## Cuidados com direitos autorais

Não faça download indiscriminado de fotografias encontradas na internet para redistribuição.

Para um protótipo privado, registre sempre:
- URL de origem;
- autor ou veículo;
- data;
- informação sobre licença quando disponível.

Para disponibilização pública do Meu Time IA, dê preferência a imagens:
- próprias;
- licenciadas;
- autorizadas;
- disponibilizadas para reutilização.

## Uso futuro no RAG

Na primeira versão do Meu Time IA, o RAG pode trabalhar apenas com texto.

As imagens podem ser utilizadas posteriormente de três formas:

1. retornar uma imagem relacionada à resposta;
2. usar metadados da imagem para busca;
3. usar um modelo multimodal para interpretar conteúdo visual.

Exemplo:

Pergunta:
“Quem foi o maior ídolo do Flamengo?”

Resposta textual:
“Zico.”

Resultado multimídia futuro:
- texto sobre Zico;
- imagem de Zico;
- fonte da imagem.
