import json
import unittest
from pathlib import Path

from lab_topic_graph.topic_graph_safe import classify_article


REGISTRY_PATH = Path("lab_topic_graph/config/cluster_registry.lab.json")


class TaxonomyRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_plural_lencois_is_classified(self):
        result = classify_article(
            {
                "titulo": "Como escolher lençóis queen com elástico para maior conforto",
                "categoria": "Quarto",
            },
            self.registry,
        )
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(result.cluster_id, "quarto-cama-textil")

    def test_generic_preparar_drinks_is_not_meal_prep(self):
        result = classify_article(
            {
                "titulo": "Como preparar drinks caseiros com mais facilidade",
                "categoria": "Cozinha",
            },
            self.registry,
        )
        self.assertEqual(result.status, "APPROVED")
        self.assertEqual(result.cluster_id, "cozinha-bebidas")
        self.assertNotEqual(result.cluster_id, "cozinha-preparo-refeicoes")


if __name__ == "__main__":
    unittest.main()
