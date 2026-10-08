# Guia prático — Branches, Pull Requests e Merge no Git

**Projeto:** Meu Time IA  
**Repositório:** https://github.com/silviolima07/meu_time_ai  
**Ambiente:** VS Code no Windows conectado por Remote-SSH ao Ubuntu  
**Pasta do projeto:** `/home/silvio/projetos/meu_time_ai`

## 1. Conceitos essenciais

| Termo | Significado |
|---|---|
| `main` | Branch principal, que deve permanecer estável. |
| Branch de trabalho | Linha de desenvolvimento separada para uma funcionalidade ou correção. |
| Working tree | Arquivos locais que você está editando. |
| Staging (`git add`) | Seleção das alterações que entrarão no próximo commit. |
| Commit | Registro de um conjunto de alterações no histórico local. |
| Push | Envio dos commits locais ao repositório remoto (GitHub). |
| Pull Request (PR) | Proposta de incorporar uma branch em outra, com revisão das diferenças. |
| Merge | Incorporação das alterações da branch à `main`. |
| Pull | Busca e integra atualizações remotas à branch local. |

**Regra prática:** crie uma branch por funcionalidade, correção ou tarefa relacionada — não por arquivo e nem obrigatoriamente por commit.

## 2. Antes de começar uma tarefa

Abra o terminal do VS Code conectado ao Ubuntu:

```bash
cd ~/projetos/meu_time_ai
git status
git branch --show-current
```

Confira se há modificações locais. **Não descarte arquivos sem saber o que são.** Se a árvore de trabalho estiver limpa, atualize a principal:

```bash
git switch main
git pull origin main
```

Se `git switch` reclamar de alterações locais, pare e avalie se devem ser registradas, guardadas com `git stash` ou preservadas de outra forma.

## 3. Criar uma branch nova

Exemplo para implementar cache no RAG:

```bash
git switch -c feature/cache-rag
```

Confirme:

```bash
git branch --show-current
git status
```

Sugestões de nomes:

- `feature/cache-rag` — funcionalidade nova.
- `fix/erro-audio` — correção de defeito.
- `docs/atualiza-readme` — documentação.
- `chore/organiza-gitignore` — manutenção.

## 4. Alterar o código e verificar

Edite os arquivos no VS Code e execute:

```bash
git status
git diff
```

Para conferir um arquivo específico:

```bash
git diff -- scripts/09_telegram_pipeline.py
```

Se a alteração envolver Python, valide ao menos a sintaxe:

```bash
python -m py_compile scripts/09_telegram_pipeline.py
```

**Atenção:** `py_compile` sem saída significa apenas que não foram encontrados erros de sintaxe; isso não substitui testes funcionais.

## 5. Cuidados especiais com o bot em execução

O serviço `meu-time-ia.service` executa:

```text
/home/silvio/projetos/meu_time_ai/scripts/09_telegram_pipeline.py
```

O serviço **não sabe qual branch está ativa**: ele lê os arquivos dessa pasta. Reiniciá-lo durante o desenvolvimento pode colocar a versão experimental no ar, mesmo sem commit ou merge.

Para verificar o serviço:

```bash
systemctl status meu-time-ia.service --no-pager
journalctl -u meu-time-ia.service -n 30 --no-pager
```

Somente quando for apropriado testar no bot em execução:

```bash
sudo systemctl restart meu-time-ia.service
```

Evite executar outra instância de polling simultaneamente. Para maior segurança, considere no futuro separar pastas e configurações de **desenvolvimento** e **produção**.

## 6. Preparar e criar o commit

Revise o que será incluído. Prefira selecionar arquivos específicos:

```bash
git status
git add scripts/09_telegram_pipeline.py
git diff --cached
```

Se estiver correto:

```bash
git commit -m "Adiciona funcionalidade ao bot Telegram"
```

É possível criar **vários commits na mesma branch** enquanto trabalha na funcionalidade.

## 7. Enviar a branch ao GitHub

Na primeira publicação da branch:

```bash
git push -u origin feature/cache-rag
```

Nos próximos envios da mesma branch, normalmente basta:

```bash
git push
```

O `push` da branch **não altera a `main`**.

## 8. Abrir e revisar o Pull Request

1. Acesse o repositório no GitHub.
2. Clique em **Compare & pull request** ou abra a aba **Pull requests → New pull request**.
3. Confirme **base: `main`** e **compare: `feature/cache-rag`**.
4. Escreva um título objetivo e uma descrição das alterações e testes.
5. Clique em **Create pull request**.
6. Confira a aba **Files changed** para verificar os arquivos e linhas alterados.
7. Aguarde os checks e a verificação de conflitos. Se a página ficar presa em *Checking for the ability to merge automatically...*, tente atualizar com `F5`.

**Não confunda:** *All checks have passed* não garante que a funcionalidade inteira esteja correta; significa apenas que as verificações configuradas passaram.

## 9. Fazer o merge no GitHub

Depois da revisão e dos testes:

1. Confira que o PR aponta para a `main` correta.
2. Verifique que não há conflitos impeditivos.
3. Clique em **Merge pull request**.
4. Clique em **Confirm merge**.
5. Aguarde a confirmação **Successfully merged**.

Se houver conflitos, resolva-os antes do merge. Não force a integração sem entender as diferenças.

## 10. Atualizar a `main` no Ubuntu

Após o merge:

```bash
git switch main
git pull origin main
git status
```

Resultado ideal:

```text
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

Se o `git status` mostrar arquivos não monitorados ou modificados, **isso não significa necessariamente que o pull falhou**. Significa que existem mudanças locais a analisar. Verifique também se o PR foi realmente integrado: um `Already up to date` pode indicar que o merge ainda não aconteceu.

## 11. Limpar branches antigas (opcional)

Depois de confirmar o merge e a atualização da `main`:

```bash
git branch -d feature/cache-rag
```

Para remover a branch remota, se não for mais necessária:

```bash
git push origin --delete feature/cache-rag
```

A exclusão da branch **não apaga os commits já incorporados à `main`**. Não use `git branch -D` sem entender por que o Git está impedindo a exclusão.

## 12. Fluxo resumido para copiar e reutilizar

Substitua `feature/minha-funcionalidade` e os nomes dos arquivos pelos da nova tarefa.

```bash
# 1. Começar a partir da main atualizada
cd ~/projetos/meu_time_ai
git status
git switch main
git pull origin main

# 2. Criar branch
git switch -c feature/minha-funcionalidade

# 3. Editar e testar o código no VS Code
# ...
git diff
git status

# 4. Selecionar somente os arquivos da tarefa
git add CAMINHO_DO_ARQUIVO
git diff --cached

# 5. Registrar e publicar
git commit -m "Descreve a alteração"
git push -u origin feature/minha-funcionalidade

# 6. Criar PR no GitHub: feature/minha-funcionalidade -> main
# 7. Revisar, testar e confirmar o merge no GitHub

# 8. Sincronizar a main local
git switch main
git pull origin main
git status
```

## 13. Erros e dúvidas frequentes

**`git status` mostra arquivos não monitorados:** são arquivos locais ainda não adicionados ao Git. Avalie se devem ser versionados ou ignorados pelo `.gitignore`.

**`git status` mostra `deleted:`:** o arquivo monitorado foi removido localmente. Se a remoção for intencional, registre-a no commit; se não, investigue antes de restaurar.

**`.gitignore` não ignora arquivo já versionado:** regras de ignore afetam normalmente arquivos não monitorados. Para retirar um arquivo do índice preservando sua cópia local, use `git rm --cached CAMINHO`, com cuidado e em uma alteração deliberada.

**`git pull` diz `Already up to date`, mas a alteração não aparece:** confira se o Pull Request foi efetivamente integrado à `main` e se está no repositório correto.

**Posso alterar diretamente a `main`?** Sim, se as regras do repositório permitirem. Em tarefas importantes, prefira branch + PR; em mudanças triviais, a decisão depende do nível de controle desejado.

**Posso fazer vários commits na mesma branch?** Sim. É o normal durante uma tarefa maior.

## 14. Exemplos reais que praticamos

| PR | Branch | Objetivo |
|---|---|---|
| #1 | `feature/telegram-menu` | Menu nativo e comando `/ajuda` do Telegram. |
| #2 | `chore/remove-telegram-script-antigo` | Remover script antigo do pipeline. |
| #3 | `chore/gitignore-modelos` | Ignorar diretórios locais de modelos e testes. |

**Lembrete final:** a branch separa o **histórico do Git**, não cria automaticamente um ambiente de execução isolado. No Meu Time IA, isso é especialmente importante porque o systemd usa a mesma pasta de trabalho.
