import unittest
from scripts.proveniencia import extrair_fontes_ids

class TestProvenienciaChunks(unittest.TestCase):
    def test_fontes_isoladas_por_secao(self):
        secao_fundacao = "## Fundação\nTexto histórico.\nFontes: FLA-HIS-001"
        secao_estadio = "## Estádio\nTexto sobre o estádio."
        self.assertEqual(extrair_fontes_ids(secao_fundacao), ["FLA-HIS-001"])
        self.assertEqual(extrair_fontes_ids(secao_estadio), [])

    def test_secao_sem_fontes(self):
        resultado = extrair_fontes_ids("## História\nTexto sem referências.")
        self.assertEqual(resultado, [])

    def test_extrair_duas_fontes_sem_duplicacao(self):
        texto = "## Fundação\nTexto histórico.\nFontes: FLA-HIS-001, FLA-HIS-002, FLA-HIS-001"
        resultado = extrair_fontes_ids(texto)
        self.assertEqual(resultado, ["FLA-HIS-001", "FLA-HIS-002"])

if __name__ == "__main__":
    unittest.main()
