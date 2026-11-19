"""C66 — os cabeçalhos UNIVERSAIS precisam respeitar a ordem do prompt."""
import inspect
import re
import unittest

from affiliate_hub_v31 import automatic_blogger_drafts as blogger
from affiliate_hub_v31 import automatic_wordpress_drafts as wordpress
from affiliate_hub_v31.tests.test_automatic_wordpress_drafts import paras


class EditorialHeadingOrderTests(unittest.TestCase):
    def test_real_ai_json_requires_exactly_eight_ordered_parts(self):
        src=inspect.getsource(blogger.generate_original_paragraphs)
        self.assertIn("EXATAMENTE 8 parágrafos",src)
        self.assertIn("ORDEM OBRIGATÓRIA",src)
        self.assertIn("1) objetivo e necessidade",src)
        self.assertIn("3) compatibilidade",src)
        self.assertIn("4) materiais",src)
        self.assertIn("6) erros comuns",src)
        self.assertIn("7) como conferir",src)
        self.assertIn("8) conclusão",src)
        self.assertIn('"minItems":8,"maxItems":8',src)

    def test_shared_eight_headings_match_real_ai_order(self):
        h=blogger.editorial_headings(8)
        self.assertEqual(len(h),8)
        for index, marker in (
            (0,"escolha"),(1,"Medidas"),(2,"Compatibilidade"),
            (3,"Materiais"),(4,"Cuidados"),(5,"Erros"),
            (6,"anúncio"),(7,"Conclusão"),
        ):
            self.assertIn(marker,h[index])

    def test_wordpress_html_no_longer_labels_style_as_material(self):
        plan={"status":"READY_FOR_DRAFT_REVIEW",
              "title":"Vaso Decorativo",
              "related":[], "offer_html":"<section>Oferta segura</section>"}
        body=wordpress.compose_article(
            plan,paras(),site_url="https://example.test/")
        editorial=body.split("</section>")[0]
        headers=re.findall(r"<h2>([^<]*)</h2>",editorial)
        self.assertEqual(headers,list(blogger.editorial_headings(8)))
        self.assertIn("Compatibilidade",headers[2])
        self.assertEqual(headers[7],"Conclusão")
        self.assertNotIn("Perguntas para o anúncio",editorial)
        self.assertNotIn("Comparação de especificações",editorial)

    def test_blogger_uses_exactly_the_same_heading_order(self):
        plan={"status":"READY_FOR_ORIGINAL_DRAFT_REVIEW",
              "title":"Guia de produto", "product_title":"Objeto para o lar",
              "offer_html":"<section>Oferta segura</section>"}
        body=blogger.compose_draft_html(
            plan,paras(),blog_home_url="https://example.blogspot.com/",
            published_posts=[])
        headers=re.findall(r"<h2>([^<]*)</h2>",body)
        self.assertEqual(headers,list(blogger.editorial_headings(8)))
        self.assertEqual(headers[-1],"Conclusão")

    def test_nonstandard_old_writer_length_does_not_mislabel_last(self):
        for n in (6,7,9,10):
            with self.subTest(n=n):
                h=blogger.editorial_headings(n)
                self.assertEqual(len(h),n)
                self.assertEqual(h[-1],"Conclusão")
        with self.assertRaises(blogger.AutoDraftError):
            blogger.editorial_headings(5)
        with self.assertRaises(blogger.AutoDraftError):
            blogger.editorial_headings(True)


if __name__=="__main__":
    unittest.main()
