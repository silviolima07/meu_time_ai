from pathlib import Path
import json
import re


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PASTA_PROCESSADOS = ROOT / "dados_processados"
PASTA_CHUNKS = PASTA_PROCESSADOS / "chunks"

ARQUIVO_ENTRADA = PASTA_PROCESSADOS / "documentos.json"
ARQUIVO_SAIDA = PASTA_CHUNKS / "chunks.json"


# ============================================================
# GARANTIR ESTRUTURA
# ============================================================

PASTA_CHUNKS.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# VALIDAR ENTRADA
# ============================================================

if not ARQUIVO_ENTRADA.exists():

    print("[ERRO] documentos.json não encontrado.")
    print("\nExecute primeiro:")
    print("python .\\scripts\\01_carregar_documentos.py")

    raise SystemExit(1)


# ============================================================
# CARREGAR DOCUMENTOS
# ============================================================

with open(
    ARQUIVO_ENTRADA,
    "r",
    encoding="utf-8"
) as arquivo:

    documentos = json.load(arquivo)


print("=" * 70)
print("02 - CRIAÇÃO DE CHUNKS POR SEÇÃO / PARÁGRAFO")
print("=" * 70)

print(f"\nDocumentos recebidos: {len(documentos)}\n")


# ============================================================
# LIMPEZA
# ============================================================

def limpar_texto(texto: str) -> str:

    texto = texto.replace("\r\n", "\n")

    texto = re.sub(
        r"\n{3,}",
        "\n\n",
        texto
    )

    return texto.strip()


# ============================================================
# CRIAÇÃO DOS CHUNKS
# ============================================================

def criar_chunks_markdown(texto: str):

    """
    Cria chunks respeitando a estrutura Markdown.

    Cada título Markdown (#, ##, ### etc.) inicia
    um novo bloco.

    O conteúdo abaixo do título permanece associado
    àquela seção até aparecer o próximo título.
    """

    linhas = texto.splitlines()

    chunks = []

    bloco_atual = []

    titulo_atual = None


    for linha in linhas:

        linha_limpa = linha.strip()

        # Detecta heading Markdown
        if re.match(r"^#{1,6}\s+", linha_limpa):

            # Salva seção anterior
            if bloco_atual:

                texto_bloco = "\n".join(
                    bloco_atual
                ).strip()

                if texto_bloco:

                    chunks.append(
                        {
                            "titulo": titulo_atual,
                            "texto": texto_bloco
                        }
                    )

            # Inicia nova seção
            titulo_atual = re.sub(
                r"^#{1,6}\s+",
                "",
                linha_limpa
            )

            bloco_atual = [
                linha_limpa
            ]

        else:

            # Conteúdo pertencente à seção atual
            if linha_limpa or bloco_atual:

                bloco_atual.append(
                    linha
                )


    # Salvar último bloco
    if bloco_atual:

        texto_bloco = "\n".join(
            bloco_atual
        ).strip()

        if texto_bloco:

            chunks.append(
                {
                    "titulo": titulo_atual,
                    "texto": texto_bloco
                }
            )


    return chunks


# ============================================================
# PROCESSAMENTO
# ============================================================

todos_chunks = []

chunk_global_id = 0


for documento in documentos:

    texto = limpar_texto(
        documento["texto"]
    )

    chunks_documento = criar_chunks_markdown(
        texto
    )

    print(
        f"{documento['arquivo']:<25}"
        f" -> {len(chunks_documento):>3} chunks"
    )


    for indice, bloco in enumerate(
        chunks_documento
    ):

        texto_chunk = bloco["texto"]

        chunk = {

            "chunk_id": chunk_global_id,

            "chunk_documento": indice,

            "time": documento["time"],

            "arquivo": documento["arquivo"],

            "categoria": documento["categoria"],

            "secao": bloco["titulo"],

            "texto": texto_chunk,

            "tamanho_caracteres": len(
                texto_chunk
            )
        }

        todos_chunks.append(
            chunk
        )

        chunk_global_id += 1


# ============================================================
# VALIDAÇÃO
# ============================================================

if not todos_chunks:

    print("\n[ERRO] Nenhum chunk foi criado.")

    raise SystemExit(1)


# ============================================================
# SALVAR
# ============================================================

with open(
    ARQUIVO_SAIDA,
    "w",
    encoding="utf-8"
) as arquivo:

    json.dump(
        todos_chunks,
        arquivo,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# RESUMO
# ============================================================

print("\n" + "=" * 70)

print(
    f"Total de chunks criados: "
    f"{len(todos_chunks)}"
)

print("\nArquivo gerado:")
print(ARQUIVO_SAIDA)

print("=" * 70)


# ============================================================
# EXEMPLOS
# ============================================================

print("\nEXEMPLOS DOS PRIMEIROS CHUNKS")
print("-" * 70)


for chunk in todos_chunks[:5]:

    print(
        f"\nchunk_id: {chunk['chunk_id']}"
    )

    print(
        f"arquivo: {chunk['arquivo']}"
    )

    print(
        f"seção: {chunk['secao']}"
    )

    print(
        f"tamanho: "
        f"{chunk['tamanho_caracteres']} caracteres"
    )

    print("\nTexto:")
    print(chunk["texto"])

    print("-" * 70)