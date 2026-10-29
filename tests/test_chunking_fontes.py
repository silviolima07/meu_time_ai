import unittest
from scripts.chunking import criar_chunks_markdown
from scripts.proveniencia import extrair_fontes_ids

class TestChunkingFontes(unittest.TestCase):
    def test_fontes_por_chunk(self):
        texto = "## Fundação\nClube fundado em 1912.\nFontes: SAN-HIS-001\n\n## Estádio\nInformações sobre o estádio."
        chunks = criar_chunks_markdown(texto)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["titulo"], "Fundação")
        self.assertEqual(chunks[1]["titulo"], "Estádio")
        self.assertEqual(extrair_fontes_ids(chunks[0]["texto"]), ["SAN-HIS-001"])
        self.assertEqual(extrair_fontes_ids(chunks[1]["texto"]), [])

if __name__ == "__main__":
    unittest.main()
