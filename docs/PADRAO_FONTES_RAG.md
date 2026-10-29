# Padrão de Fontes e Rastreabilidade — Meu Time IA

## Objetivo

Garantir que as informações utilizadas pelo RAG sejam verificáveis, atualizadas quando necessário e rastreáveis até suas fontes originais.

## Regras obrigatórias

1. Priorizar fontes primárias: clubes, federações, confederações e organizadores das competições.
2. Registrar URLs específicas que sustentem as afirmações, evitando referências genéricas à página inicial.
3. Verificar fatos históricos antes de incorporá-los à base de conhecimento.
4. Registrar a data de referência de informações que mudam com o tempo.
5. Documentar divergências entre fontes, sem apresentar dados controversos como fatos incontroversos.
6. Preservar a identificação da fonte nos metadados dos chunks durante a indexação.
7. Revisar os documentos antes de regenerar os índices BM25 e ChromaDB.

## Situação inicial

- Flamengo: corpus existente, pendente de auditoria das fontes.
- Santos: corpus em construção, sujeito a este padrão desde o início.
- Índices de produção: permanecerão inalterados durante a auditoria.

## Registro das fontes

Cada fonte deve conter:
- ID único por clube e documento (exemplo: FLA-HIS-001).
- Instituição responsável e título da publicação.
- URL específica e verificável.
- Data de publicação, quando disponível.
- Data de consulta, registrada após verificação efetiva.
- Seções e afirmações sustentadas pela fonte.

## Proveniência nos chunks

- Preservar o ID da fonte e a identificação do documento.
- Associar cada chunk às fontes que sustentam seu conteúdo.
- Não atribuir automaticamente todas as fontes do documento a todos os chunks.
- Registrar ausência ou divergência de evidências.
- Validar a proveniência antes de atualizar os índices de produção.

## Implementação inicial — proveniência dos chunks

- scripts/proveniencia.py: extrai IDs de linhas Fontes: e remove duplicações.
- scripts/chunking.py: função reutilizável de divisão Markdown por seções.
- scripts/02_criar_chunks.py: adiciona fontes_ids a cada chunk.
- Seções sem referências recebem fontes_ids vazio.

## Testes automatizados

- tests/test_proveniencia_chunks.py: 3 testes aprovados.
- tests/test_integracao_proveniencia.py: 1 teste estrutural aprovado.
- tests/test_chunking_fontes.py: 1 teste funcional aprovado.
- Total: 5 testes aprovados.

## Limitações e próximos passos

- Os testes ainda não executam o pipeline completo de ingestão.
- Os IDs declarados ainda não comprovam a veracidade das fontes.
- Auditar as referências históricas do Flamengo e do Santos.
- Validar a preservação dos metadados nos índices de recuperação.
- Não regenerar os índices de produção antes da validação completa.

## Hierarquia de fontes por assunto

- História institucional: site oficial do clube, museu e documentos históricos.
- Competições nacionais: CBF e regulamentos oficiais.
- Competições internacionais: CONMEBOL e FIFA.
- Estatísticas históricas: registros oficiais e publicações especializadas verificáveis.
- Informações atuais: fontes oficiais com data de atualização.

## Critérios de validação

1. A URL deve estar acessível.
2. O conteúdo deve sustentar explicitamente a afirmação.
3. Registrar a data da consulta.
4. Identificar quais afirmações são sustentadas por cada fonte.
5. Manter como pendentes as informações sem comprovação.
6. Não confundir uma fonte institucional confiável com uma evidência específica.
