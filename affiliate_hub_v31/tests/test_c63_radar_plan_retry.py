"""C63: recuperar título editorial Radar sem baixar o gate ou publicar."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RADAR_SRC = Path(__file__).resolve().parents[2] / "radar_tech_br" / "src"
if str(RADAR_SRC) not in sys.path:
    sys.path.insert(0, str(RADAR_SRC))
import generate_articles as radar


ITEM = {
    "product": "Organizador de Louças Dobrável",
    "source_keyword": "organizador cozinha",
    "category": "Cozinha & Utilidades",
}


def answer(title):
    return json.dumps({
        "title": title,
        "keyword": "organização da cozinha",
        "reader_need": "Entender critérios para organizar louças.",
        "product_connection": "Um organizador é uma opção relacionada.",
    }, ensure_ascii=False)


class RadarPlanRecoveryTests(unittest.TestCase):
    def test_short_31_character_title_retries_with_consistent_gate(self):
        short = "Como organizar louças na cozinha"  # curto: não é aceito
        self.assertLess(len(short), 35)
        valid = "Como organizar louças em cozinhas compactas"
        self.assertGreaterEqual(len(valid), 35)
        self.assertLessEqual(len(valid), 60)
        with patch.object(radar, "ai", side_effect=[answer(short), answer(valid)]) as fake:
            result = radar.make_plan(ITEM)
        self.assertEqual(result["title"], valid)
        self.assertEqual(fake.call_count, 2)
        prompt = fake.call_args_list[1].args[0]
        self.assertIn("\n\nCORREÇÃO OBRIGATÓRIA", prompt)
        self.assertIn("entre 35 e 60 caracteres", prompt)
        self.assertNotIn("\\nCORREÇÃO", prompt)

    def test_after_three_bad_titles_blocks_without_fallback(self):
        short = answer("Organize melhor sua cozinha")
        with patch.object(radar, "ai", side_effect=[short, short, short]) as fake:
            with self.assertRaisesRegex(RuntimeError, "após 3 tentativas"):
                radar.make_plan(ITEM)
        self.assertEqual(fake.call_count, 3)

    def test_61_character_title_cannot_bypass_initial_limit(self):
        invalid = answer("A" * 61)
        with self.assertRaisesRegex(RuntimeError, "fora da faixa"):
            radar.make_plan(ITEM, invalid)

if __name__ == "__main__":
    unittest.main()
