from pathlib import Path


# ============================================================
# DIRETÓRIO RAIZ DO PROJETO
# ============================================================

ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# PASTAS NECESSÁRIAS
# ============================================================

PASTAS = [
    ROOT / "scripts",
    ROOT / "flamengo",
    ROOT / "dados_processados",
    ROOT / "dados_processados" / "chunks",
    ROOT / "dados_processados" / "embeddings",
    ROOT / "chroma_db",
]


# ============================================================
# CRIAÇÃO / VERIFICAÇÃO
# ============================================================

print("=" * 60)
print("CONFIGURAÇÃO DA ESTRUTURA DO PROJETO")
print("=" * 60)

print(f"\nDiretório raiz:\n{ROOT}\n")


for pasta in PASTAS:

    if pasta.exists():

        print(f"[OK]     {pasta.relative_to(ROOT)}")

    else:

        pasta.mkdir(
            parents=True,
            exist_ok=True
        )

        print(f"[CRIADA] {pasta.relative_to(ROOT)}")


print("\n" + "=" * 60)
print("Estrutura verificada com sucesso.")
print("=" * 60)