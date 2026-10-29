import re

def extrair_fontes_ids(texto: str) -> list[str]:
    """Extrai IDs declarados em linhas Fontes: do Markdown."""
    ids = []
    padrao = r"\b[A-Z]{3}-[A-Z]{3}-[0-9]{3}\b"
    for linha in texto.splitlines():
        if re.match(r"^\s*Fontes:\s*", linha, re.IGNORECASE):
            for fonte_id in re.findall(padrao, linha):
                if fonte_id not in ids:
                    ids.append(fonte_id)
    return ids
