"""Testes funcionais de roteamento BM25 e ChromaDB por clube."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rag_core import busca_bm25, busca_vetorial, busca_hibrida, obter_colecao


class TestRoteamentoTimes(unittest.TestCase):

    PERGUNTA = "Quais são os títulos do Flamengo?"

    def test_bm25_compatibilidade_flamengo(self):
        antigo = busca_bm25(self.PERGUNTA)
        novo = busca_bm25(self.PERGUNTA, time_id="flamengo")

        self.assertEqual(antigo, novo)
        self.assertEqual(len(novo), 5)

    def test_bm25_santos_sem_indice(self):
        with self.assertRaises(FileNotFoundError):
            busca_bm25(self.PERGUNTA, time_id="santos")

    def test_vetorial_compatibilidade_flamengo(self):
        antigo = busca_vetorial(self.PERGUNTA)
        novo = busca_vetorial(self.PERGUNTA, time_id="flamengo")

        self.assertEqual(antigo, novo)
        self.assertEqual(len(novo), 5)

    def test_vetorial_santos_sem_colecao(self):
        with self.assertRaises(Exception) as contexto:
            obter_colecao("santos")

        self.assertEqual(
            type(contexto.exception).__name__,
            "NotFoundError"
        )

    def test_clube_invalido(self):
        with self.assertRaises(ValueError):
            obter_colecao("time_inexistente")


    def test_hibrida_compatibilidade_flamengo(self):
        """Verifica compatibilidade da recuperação híbrida com Flamengo."""
        antigo = busca_hibrida(self.PERGUNTA)
        novo = busca_hibrida(self.PERGUNTA, time_id="flamengo")

        self.assertEqual(antigo, novo)
        self.assertEqual(len(novo), 3)


if __name__ == "__main__":
    unittest.main()
