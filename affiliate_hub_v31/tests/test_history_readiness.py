"""C13: inventário de originais locais, sem PII nos logs e sem writes."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.history_readiness import audit_project, audit_all


class HistoricalReadinessTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.project=self.root/"sample"
        (self.project/"data/generated").mkdir(parents=True)
        self.history=self.project/"data/publication_history.json"
        self.generated=self.project/"data/generated"

    def write_history(self,records):
        self.history.write_text(json.dumps({"items":records}),encoding="utf-8")

    def write_article(self,name,product,title,body):
        (self.generated/name).write_text(json.dumps({
            "shopee_item_id":product,"editorial_title":title,
            "editorial_html":"<p>"+("Técnicas e orientações úteis para uso doméstico. "*30 if body else "")+"</p>"
        }),encoding="utf-8")

    def test_matching_prior_body_qualifies_one_product_without_posting(self):
        title="Como organizar a bancada com produtos selecionados"
        self.write_history([
            {"shopee_item_id":"104","editorial_title":title,
             "wordpress_url":"https://site.example.invalid/artigo"},
            {"shopee_item_id":"105","editorial_title":"Como limpar o armário antigo"},
        ])
        self.write_article("001.json","104",title,True)
        result=audit_project(self.project)
        self.assertEqual(result["records"],2)
        self.assertEqual(result["reusable_products_with_verified_body"],1)
        self.assertEqual(result["single_publication_products_missing_matching_body"],1)
        self.assertEqual(result["publication_calls"],0)
        self.assertNotIn("artigo",json.dumps(result))
        self.assertNotIn("104",json.dumps(result))

    def test_missing_history_does_not_invent_reusable_products(self):
        self.assertEqual(audit_project(self.project)["state"],"NO_HISTORY")

    def test_multiple_articles_and_duplicate_title_do_not_count_as_eligible(self):
        same="Guia de iluminação para pequenos ambientes"
        self.write_history([
            {"shopee_item_id":"107","editorial_title":same},
            {"shopee_item_id":"107","editorial_title":same},
        ])
        self.write_article("001.json","107",same,True)
        result=audit_project(self.project)
        self.assertEqual(result["reusable_products_with_verified_body"],0)
        self.assertEqual(result["products_with_multiple_publications"],1)
        self.assertEqual(result["products_with_repeated_title"],1)

    def test_bad_history_schema_fail_closed(self):
        self.history.write_text("[]",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"history_schema_invalid"):
            audit_project(self.project)

    def test_root_site_profiles_are_configurable(self):
        profiles={
            "wordpress_sample":{
                "config":"sample/config/shopee_oportunidades.json"
            },
            "wordpress_radartechbr":{
                "config":"config/shopee_oportunidades.json"
            }
        }
        self.write_history([])
        summary=audit_all(self.root,profiles=profiles)
        self.assertEqual(summary["sites_checked"],2)
        states={r["site_key"]:r["state"] for r in summary["sites"]}
        self.assertEqual(states["wordpress_sample"],"AUDITED")
        self.assertEqual(states["wordpress_radartechbr"],"NOT_LEGACY_QUEUE_PROJECT")


if __name__=="__main__":
    unittest.main()
