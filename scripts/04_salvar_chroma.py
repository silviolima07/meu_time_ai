from pathlib import Path
import json
import numpy as np
import chromadb


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

PASTA_EMBEDDINGS = ROOT / "dados_processados" / "embeddings"
PASTA_CHROMA = ROOT / "chroma_db"

ARQUIVO_EMBEDDINGS = PASTA_EMBEDDINGS / "embeddings.npy"
ARQUIVO_METADATA = PASTA_EMBEDDINGS / "metadata.json"

NOME_COLECAO = "flamengo"


# ============================================================
# GARANTIR ESTRUTURA
# ============================================================

PASTA_CHROMA.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# VALIDAR ENTRADAS
# ============================================================

if not ARQUIVO_EMBEDDINGS.exists():

    print("[ERRO] embeddings.npy não encontrado.")
    print("\nExecute primeiro:")
    print("python .\\scripts\\03_gerar_embeddings.py")

    raise SystemExit(1)


if not ARQUIVO_METADATA.exists():

    print("[ERRO] metadata.json não encontrado.")

    raise SystemExit(1)


# ============================================================
# CARREGAR EMBEDDINGS
# ============================================================

embeddings = np.load(
    ARQUIVO_EMBEDDINGS
)


# ============================================================
# CARREGAR METADADOS
# ============================================================

with open(
    ARQUIVO_METADATA,
    "r",
    encoding="utf-8"
) as arquivo:

    metadata = json.load(arquivo)


# ============================================================
# VALIDAÇÃO
# ============================================================

if len(embeddings) != len(metadata):

    raise RuntimeError(
        "Quantidade de embeddings diferente "
        "da quantidade de metadados."
    )


print("=" * 70)
print("04 - SALVAR EMBEDDINGS NO CHROMADB")
print("=" * 70)

print(f"\nEmbeddings recebidos: {len(embeddings)}")
print(f"Dimensão: {embeddings.shape[1]}")
print(f"Coleção: {NOME_COLECAO}")


# ============================================================
# CLIENTE CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path=str(PASTA_CHROMA)
)


# ============================================================
# REMOVER COLEÇÃO ANTIGA
# ============================================================

colecoes = [
    colecao.name
    for colecao in client.list_collections()
]


if NOME_COLECAO in colecoes:

    print(
        f"\nRemovendo coleção antiga: "
        f"{NOME_COLECAO}"
    )

    client.delete_collection(
        name=NOME_COLECAO
    )

    print("[OK] Coleção antiga removida.")


# ============================================================
# CRIAR COLEÇÃO NOVA
# ============================================================

print(
    f"\nCriando nova coleção: "
    f"{NOME_COLECAO}"
)

collection = client.create_collection(
    name=NOME_COLECAO,
    metadata={
        "hnsw:space": "cosine"
    }
)

print("[OK] Nova coleção criada.")


# ============================================================
# PREPARAR DADOS
# ============================================================

ids = []
documents = []
metadatas = []
embeddings_lista = []


for vetor, item in zip(
    embeddings,
    metadata
):

    chunk_id = item["chunk_id"]

    ids.append(
        f"chunk_{chunk_id}"
    )

    documents.append(
        item["texto"]
    )


    metadata_chroma = {
        "chunk_id": chunk_id,
        "chunk_documento": item["chunk_documento"],
        "time": item["time"],
        "arquivo": item["arquivo"],
        "categoria": item["categoria"],
        "tamanho_caracteres": item["tamanho_caracteres"]
    }


    # Novo metadado criado no script 02
    if "secao" in item:

        metadata_chroma["secao"] = (
            item["secao"]
            if item["secao"] is not None
            else ""
        )


    metadatas.append(
        metadata_chroma
    )

    embeddings_lista.append(
        vetor.tolist()
    )


# ============================================================
# SALVAR NO CHROMA
# ============================================================

print(
    f"\nSalvando {len(ids)} registros "
    f"no ChromaDB..."
)


collection.add(
    ids=ids,
    embeddings=embeddings_lista,
    documents=documents,
    metadatas=metadatas
)


# ============================================================
# VERIFICAÇÃO
# ============================================================

quantidade = collection.count()


print("\n" + "=" * 70)

print(
    f"Registros armazenados: "
    f"{quantidade}"
)

print(f"\nBanco vetorial:")
print(PASTA_CHROMA)

print(f"\nColeção:")
print(NOME_COLECAO)

print("=" * 70)


# ============================================================
# VALIDAÇÃO DE CONSISTÊNCIA
# ============================================================

if quantidade != len(embeddings):

    raise RuntimeError(
        f"Esperados {len(embeddings)} registros, "
        f"mas o Chroma contém {quantidade}."
    )


print(
    "\n[OK] Quantidade de registros "
    "confere com os embeddings."
)


# ============================================================
# TESTE DE LEITURA
# ============================================================

resultado = collection.get(
    ids=["chunk_0"]
)


print("\nEXEMPLO DE REGISTRO")
print("-" * 70)


if resultado["ids"]:

    print(
        f"ID: "
        f"{resultado['ids'][0]}"
    )

    metadado = (
        resultado["metadatas"][0]
    )

    print(
        f"Arquivo: "
        f"{metadado['arquivo']}"
    )

    print(
        f"Categoria: "
        f"{metadado['categoria']}"
    )

    if metadado.get("secao"):

        print(
            f"Seção: "
            f"{metadado['secao']}"
        )

    print("\nTexto:")

    print(
        resultado["documents"][0]
    )

else:

    print("Nenhum registro encontrado.")


print("-" * 70)