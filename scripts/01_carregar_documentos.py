from pathlib import Path
import json


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PASTA_FLAMENGO = ROOT / "flamengo"
PASTA_PROCESSADOS = ROOT / "dados_processados"

ARQUIVO_SAIDA = PASTA_PROCESSADOS / "documentos.json"


# ============================================================
# GARANTIR QUE AS PASTAS EXISTAM
# ============================================================

PASTA_FLAMENGO.mkdir(parents=True, exist_ok=True)
PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)


# ============================================================
# CARREGAR DOCUMENTOS
# ============================================================

ARQUIVOS_PERMITIDOS = [
    "historia.md",
    "titulos.md",
    "artilheiros.md",
    "situacao_atual.md",
]

documentos = []

arquivos_md = sorted(PASTA_FLAMENGO.glob("*.md"))
arquivos_md = [arquivo for arquivo in arquivos_md if arquivo.name in ARQUIVOS_PERMITIDOS]

print("=" * 60)
print("01 - CARREGAR DOCUMENTOS")
print("=" * 60)

print(f"\nPasta de origem:\n{PASTA_FLAMENGO}")

print(f"\nArquivos encontrados: {len(arquivos_md)}\n")


for arquivo in arquivos_md:

    texto = arquivo.read_text(
        encoding="utf-8"
    )

    documento = {
        "time": "Flamengo",
        "arquivo": arquivo.name,
        "categoria": arquivo.stem,
        "caminho": str(arquivo),
        "texto": texto,
        "tamanho_caracteres": len(texto)
    }

    documentos.append(documento)

    print(
        f"[OK] {arquivo.name:<25} "
        f"{len(texto):>6} caracteres"
    )


# ============================================================
# VALIDAÇÃO
# ============================================================

if not documentos:

    print("\n[ERRO] Nenhum arquivo Markdown encontrado.")
    print(f"Verifique a pasta: {PASTA_FLAMENGO}")

    raise SystemExit(1)


# ============================================================
# SALVAR JSON PROCESSADO
# ============================================================

with open(
    ARQUIVO_SAIDA,
    "w",
    encoding="utf-8"
) as arquivo_json:

    json.dump(
        documentos,
        arquivo_json,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# RESUMO
# ============================================================

print("\n" + "=" * 60)

print(f"Documentos carregados: {len(documentos)}")
print(f"Arquivo gerado:\n{ARQUIVO_SAIDA}")

print("=" * 60)