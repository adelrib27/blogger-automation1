"""C100 — teste offline: evitar peças e insumos confundidos com produto principal."""
import unittest
from affiliate_hub_v31.c100_r2_exact_readonly import primary_product_guard


class C100PrimaryProductGuards(unittest.TestCase):
    def check(self, title, niche, expected, site="cozinha_sem_complicacao"):
        self.assertEqual(primary_product_guard(title, niche, site), expected, (title, niche, site))

    def test_air_fryers_real_units(self):
        self.check("Air Fryer Mondial AFN-80-BI Preto Inox 8L com Timer", "cozinha/air_fryers", True)
        self.check("Air Fryer Forno Oven 12L com timer Fritadeira sem óleo", "cozinha/air_fryers", True)
        self.check("Air Fryer digital 5 litros Britânia 127V", "cozinha/air_fryers", True, site="air_fryers")

    def test_air_fryers_not_cleaner_replacements(self):
        self.check("Desengordurante Spray Potente Multiuso Cozinha Fogão e Air Fryer 300ml", "cozinha/air_fryers", False)
        self.check("Puxador Cabo Para Air Fryer Mondial Af-33 Af-34 C/parafusos", "cozinha/air_fryers", False)
        self.check("Tapete Fryer Anti Aderente Silicone Para Forrar Air Fryer", "cozinha/air_fryers", False)
        self.check("Fritadeira Elétrica Inox 5 Litros Industrial Profissional Tacho redondo", "cozinha/air_fryers", False)

    def test_blender_main_vs_part(self):
        self.check("Liquidificador Oster Jarra De Vidro 2,2 Litros 1250W", "cozinha/liquidificadores", True)
        self.check("Liquidificador Britânia BLQ1280P Lâminas Inox 2,7L", "cozinha/liquidificadores", True, site="liquidificadores")
        self.check("Arraste Motor e Copo Liquidificador Arno Power Max 1000w", "cozinha/liquidificadores", False)
        self.check("Copo para Liquidificador Arno Power Max avulso", "cozinha/liquidificadores", False)

    def test_fans_and_fan_parts(self):
        self.check("Ventilador de Coluna 40cm Mondial 8 pás", "climatizacao/ventilacao", True, site="ventiladores")
        self.check("HÉLICE VENTILADOR CADENCE + BOTÃO EROS 40CM", "climatizacao/ventilacao", False, site="achados_casa")
        self.check("Ventilador De Refrigeração Alimentos Resfriamento Rápido Para Macarrão", "climatizacao/ventilacao", False, site="achados_casa")

    def test_furniture_vs_accessories(self):
        self.check("Mesa Escritório em L 150cm com gavetas", "casa/moveis", True, site="moveis")
        self.check("Cadeira de escritório ergonômica para home office", "casa/moveis", True, site="moveis")
        self.check("Capa para cadeira de escritório impermeável", "casa/moveis", False, site="moveis")
        self.check("Puxador para móveis armário 10 peças", "casa/moveis", False, site="moveis")
        self.check("Parafusos para móveis diversos", "casa/moveis", False, site="moveis")

    def test_not_over_filter_other_niches(self):
        self.check("Colmeia Organizadora de Gavetas P M G", "casa/organizacao", True, site="casa_em_ordem")


if __name__ == "__main__":
    unittest.main()
