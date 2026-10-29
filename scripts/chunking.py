import re

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
