import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "02_criar_chunks.py"

class TestIntegracaoProveniencia(unittest.TestCase):
    def test_chunk_inclui_fontes_ids(self):
        arvore = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        campos = []
        for no in ast.walk(arvore):
            if isinstance(no, ast.Dict):
                campos.extend(
                    chave.value for chave in no.keys
                    if isinstance(chave, ast.Constant)
                    and isinstance(chave.value, str)
                )
        self.assertIn("fontes_ids", campos)

if __name__ == "__main__":
    unittest.main()
