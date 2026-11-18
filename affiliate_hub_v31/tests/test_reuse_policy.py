"""C11: reutilização com título e intenção originais e histórico confiável."""
import json
import tempfile
import unittest
from pathlib import Path
from affiliate_hub_v31.reuse_policy import (
    ReuseDenied, can_queue_reuse, validate_publication, title_is_distinct,
    history_has_publication, validate_prior_editorial_body,
)


def article(title):
    return {
        "shopee_item_id":"123",
        "seo_title":title,"editorial_title":title,"topic":title,
        "focus_keyword":"luminária de leitura",
        "reader_need":"Como iluminar o canto de leitura sem ofuscamento",
        "editorial_html":"<h2>Orientações</h2><p>Conteúdo editorial independente.</p>",
    }


class ReusePolicyTests(unittest.TestCase):
    def setUp(self):
        self.old_title="Como iluminar a sala pequena com luminárias"
        self.history={"items":[{
            "shopee_item_id":"123","editorial_title":self.old_title,
            "wordpress_post_id":117,"wordpress_url":"https://example.test/post-1"
        }]}
        self.item={
            "shopee_item_id":"123","source_keyword":"luminaria led",
            "reuse_candidate":True,"prior_publication_count":1,
        }
        self.new_title="Luz indireta para leitura: como evitar reflexos"

    def test_same_product_different_angle_is_eligible(self):
        self.assertTrue(title_is_distinct(self.new_title,self.old_title))
        allowed,titles=can_queue_reuse(self.history,"123")
        self.assertTrue(allowed)
        self.assertEqual(titles,[self.old_title])
        self.assertIsNone(validate_publication(self.history,self.item,
                                               article(self.new_title)))

    def test_same_title_with_accents_and_cases_is_not_eligible(self):
        with self.assertRaisesRegex(ReuseDenied,"too_similar"):
            validate_publication(self.history,self.item,
                                 article("COMO ILUMINAR A SALA PEQUENA COM LUMINARIAS"))

    def test_near_duplicate_title_is_not_eligible(self):
        similar="Como iluminar uma sala pequena com luminárias"
        with self.assertRaisesRegex(ReuseDenied,"too_similar"):
            validate_publication(self.history,self.item,article(similar))

    def test_history_changed_concurrently_blocks_reuse(self):
        self.history["items"].append({
            "shopee_item_id":"123","editorial_title":"Critérios de Luz em Ambientes"
        })
        with self.assertRaisesRegex(ReuseDenied,"reuse_history_not_eligible"):
            validate_publication(self.history,self.item,article(self.new_title))

    def test_missing_published_title_blocks(self):
        self.history["items"][0].pop("editorial_title")
        self.assertEqual(can_queue_reuse(self.history,"123"),(False,[]))
        with self.assertRaises(ReuseDenied):
            validate_publication(self.history,self.item,article(self.new_title))

    def test_duplicate_same_item_and_title_is_idempotent(self):
        self.assertTrue(history_has_publication(self.history,"123",self.old_title))
        self.assertFalse(history_has_publication(self.history,"123",self.new_title))

    def test_product_id_does_not_bypass_other_required_fields(self):
        x=article(self.new_title)
        x["focus_keyword"]=""
        with self.assertRaisesRegex(ReuseDenied,"incomplete"):
            validate_publication(self.history,self.item,x)
        x=article(self.new_title)
        x["shopee_item_id"]="456"
        with self.assertRaisesRegex(ReuseDenied,"mismatch"):
            validate_publication(self.history,self.item,x)

    def test_reuse_requires_distinct_actual_body_not_only_new_title(self):
        root=Path(__file__).resolve().parents[2]
        config=root/"config/editorial_cross_blog_guard.json"
        old_body=("<h2>Organização da sala</h2><p>Um ambiente doméstico compacto "
                  "pode ser organizado com rotinas que valorizem a distribuição "
                  "dos móveis, o espaço para circulação e os pontos de apoio "
                  "para objetos usados durante o dia.</p>")*30
        new_body=("<h2>Leitura sem reflexos</h2><p>Ao escolher iluminação "
                  "para leitura, convém observar o posicionamento do foco "
                  "luminoso, o contraste com a página, a luz natural disponível "
                  "e a direção da luminária em relação aos olhos.</p>")*30
        with tempfile.TemporaryDirectory() as dirname:
            folder=Path(dirname)
            old={
                "shopee_item_id":"123",
                "seo_title":self.old_title,
                "editorial_title":self.old_title,
                "editorial_html":old_body
            }
            (folder/"001.json").write_text(json.dumps(old),encoding="utf-8")
            new=article(self.new_title)
            new["editorial_html"]=new_body
            self.assertIsNone(validate_prior_editorial_body(
                self.history,self.item,new,folder,config))
            new["editorial_html"]=old_body
            with self.assertRaisesRegex(ReuseDenied,"too_similar"):
                validate_prior_editorial_body(self.history,self.item,new,folder,config)
            (folder/"001.json").unlink()
            with self.assertRaisesRegex(ReuseDenied,"body_unavailable"):
                validate_prior_editorial_body(self.history,self.item,new,folder,config)

    def test_new_product_remains_unaffected_in_default_mode(self):
        item={"reuse_candidate":False,"shopee_item_id":"124"}
        self.assertIsNone(validate_publication(self.history,item,article("Sem impacto")))


if __name__=="__main__":
    unittest.main()
