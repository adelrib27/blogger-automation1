"""C36 — título genérico de qualquer tópico, sem invenção de atributos."""
import unittest

from affiliate_hub_v31.universal_brief import (
    UniversalBriefError,create_universal_brief,
)


class DynamicBriefTests(unittest.TestCase):
    def test_unanticipated_topic_is_preserved_without_predefined_taxonomy(self):
        b=create_universal_brief(topic="mesa de madeira",product_title="Mesa madeira maciça",
            product_key="shopee:100:200",article_index=1)
        self.assertIn("mesa de madeira",b["proposed_title"])
        self.assertIn("Mesa madeira maciça",b["proposed_title"])
        self.assertEqual(b["editorial_status"],"REVIEW_REQUIRED")
        self.assertFalse(b["product_specs_verified"])
        self.assertFalse(b["can_publish"])

    def test_angles_and_slug_are_distinct_by_product_and_index(self):
        a=create_universal_brief(topic="pneu de moto",product_title="Pneu",
           product_key="shopee:1:1",article_index=1)
        b=create_universal_brief(topic="pneu de moto",product_title="Pneu",
           product_key="shopee:1:2",article_index=2)
        self.assertNotEqual(a["slug"],b["slug"])
        self.assertNotEqual(a["angle"],b["angle"])

    def test_long_input_stays_within_seo_title_limit(self):
        a=create_universal_brief(topic="organização de área de serviço para casa "*3,
            product_title="Mesa para Jardim Planejado e Muito Comprida "*8,
            product_key="shopee:10:20",article_index=24)
        self.assertLessEqual(len(a["proposed_title"]),120)
        self.assertFalse(a["can_publish"])

    def test_fails_closed_on_empty_or_bad_input(self):
        base=dict(topic="mesa",product_title="Mesa de jantar",
            product_key="shopee:10:20",article_index=1)
        for change in ({"topic":" "},{"product_title":""},{"product_key":""},
                       {"article_index":0},{"article_index":25},
                       {"article_index":True},{"topic":123}):
            with self.subTest(change=change),self.assertRaises(UniversalBriefError):
                create_universal_brief(**(base|change))


if __name__=="__main__":
    unittest.main()
