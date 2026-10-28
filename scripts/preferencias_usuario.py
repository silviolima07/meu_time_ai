from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
BANCO = ROOT / "dados_processados" / "usuarios.sqlite3"

TIMES_VALIDOS = {
    "flamengo",
    "santos",
    "internacional",
    "atletico_mineiro",
}


def conectar():
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(BANCO, timeout=10)


def inicializar_banco():
    with conectar() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS preferencias_usuario (
                user_id INTEGER PRIMARY KEY,
                time_id TEXT NOT NULL
            )
        """)


def salvar_time(user_id: int, time_id: str):
    if time_id not in TIMES_VALIDOS:
        raise ValueError(f"Time inválido: {time_id}")

    inicializar_banco()

    with conectar() as conexao:
        conexao.execute("""
            INSERT INTO preferencias_usuario (user_id, time_id)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET time_id = excluded.time_id
        """, (user_id, time_id))


def obter_time(user_id: int) -> str:
    inicializar_banco()

    with conectar() as conexao:
        resultado = conexao.execute(
            "SELECT time_id FROM preferencias_usuario WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    return resultado[0] if resultado else "flamengo"
