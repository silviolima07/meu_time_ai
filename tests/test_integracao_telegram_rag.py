"""Testes leves da integração Telegram -> RAG, sem carregar modelos."""

import ast
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
ARQUIVO = ROOT / "scripts" / "09_telegram_pipeline.py"


def carregar_funcao():
    """Extrai apenas processar_pergunta, sem importar o bot."""
    arvore = ast.parse(ARQUIVO.read_text(encoding="utf-8"))
    funcao = next(
        node for node in arvore.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "processar_pergunta"
    )

    modulo = ast.Module(body=[funcao], type_ignores=[])
    codigo = compile(modulo, str(ARQUIVO), "exec")

    ambiente = {
        "time": __import__("time"),
        "busca_hibrida": Mock(return_value=["resultado"]),
        "montar_contexto": Mock(return_value="contexto"),
        "perguntar_llm": Mock(return_value="Resposta simulada"),
        "salvar_log": Mock(),
    }

    exec(codigo, ambiente)
    return ambiente["processar_pergunta"], ambiente


class TestIntegracaoTelegramRAG(unittest.TestCase):

    def setUp(self):
        self.processar, self.ambiente = carregar_funcao()

    def test_flamengo_encaminha_time_id(self):
        resposta = self.processar(
            "Quais são os títulos?",
            time_id="flamengo"
        )

        self.assertEqual(resposta, "Resposta simulada")
        self.ambiente["busca_hibrida"].assert_called_once_with(
            "Quais são os títulos?",
            time_id="flamengo"
        )
        self.ambiente["perguntar_llm"].assert_called_once()

    def test_clube_sem_base_nao_executa_rag(self):
        resposta = self.processar(
            "Quais são os títulos?",
            time_id="santos"
        )

        self.assertIn("base de conhecimento", resposta)
        self.ambiente["busca_hibrida"].assert_not_called()
        self.ambiente["perguntar_llm"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
