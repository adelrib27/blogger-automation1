"""C58 — internos universais para postagens WordPress reais."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.article_commerce import CommerceArticleError
from affiliate_hub_v31.wordpress_related_posts import from_published_history


class WordPressRelatedTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"history.json"
        self.home="https://meublog.exemplo.com.br/"
        self.posts=[
            {"wordpress_post_id":11,"editorial_title":"Guia de decoração para sala",
             "wordpress_url":self.home+"decoracao-para-sala/",
             "category":"Sala"},
            {"wordpress_post_id":12,"editorial_title":"Como escolher uma mesa",
             "wordpress_url":self.home+"como-escolher-uma-mesa/",
             "category":"Cozinha"},
            {"wordpress_post_id":13,"editorial_title":"Ideias para organizar sua sala",
             "wordpress_url":self.home+"ideias-para-organizar-sua-sala/",
             "category":"Sala"},
        ]
        self._write()

    def _write(self):
        self.path.write_text(json.dumps({"items":self.posts}),
                             encoding="utf-8")

    def test_real_same_domain_links_with_category_priority(self):
        result=from_published_history(
            self.path,blog_home_url=self.home,
            article_title="Móveis para sua casa",category="Sala")
        self.assertEqual(result.count("<li>"),2)
        self.assertIn("decoracao-para-sala/",result)
        self.assertIn("ideias-para-organizar-sua-sala/",result)
        self.assertNotIn("como-escolher-uma-mesa/",result)
        self.assertIn('data-v31-related="1"',result)

    def test_self_dedup_and_no_phantom_posts(self):
        self.posts.append(self.posts[2].copy())
        self._write()
        result=from_published_history(
            self.path,blog_home_url=self.home,
            article_title="Ideias para organizar sua sala",
            category="Sala")
        self.assertEqual(result.count("<li>"),2)
        self.assertNotIn("ideias-para-organizar-sua-sala/",result)

    def test_foreign_or_unconfirmed_links_ignored(self):
        self.posts.extend([
            {"wordpress_post_id":14,"editorial_title":"Link externo perigoso",
             "wordpress_url":"https://outro-blog.example.com/slug/",
             "category":"Sala"},
            {"wordpress_post_id":None,"editorial_title":"Post ainda não feito",
             "wordpress_url":self.home+"fantasma/", "category":"Sala"},
            {"wordpress_post_id":17,"editorial_title":"WP Admin não é artigo",
             "wordpress_url":self.home+"wp-admin/?edit=1","category":"Sala"}
        ])
        self._write()
        result=from_published_history(
            self.path,blog_home_url=self.home,
            article_title="Como mobiliar seu quarto",category="Sala",
            limit=6)
        self.assertEqual(result.count("<li>"),3)
        self.assertNotIn("fantasma",result)
        self.assertNotIn("outro-blog",result)
        self.assertNotIn("wp-admin",result)

    def test_missing_or_malformed_history_fails_closed(self):
        self.path.unlink()
        with self.assertRaisesRegex(CommerceArticleError,
                                    "publication_history_missing"):
            from_published_history(self.path,blog_home_url=self.home,
                article_title="Novo post")
        self.path.write_text("{invalid",encoding="utf-8")
        with self.assertRaisesRegex(CommerceArticleError,
                                    "publication_history_invalid"):
            from_published_history(self.path,blog_home_url=self.home,
                article_title="Novo post")

    def test_never_generates_links_for_new_blog_with_no_posts(self):
        self.posts=[]
        self._write()
        self.assertEqual(from_published_history(
            self.path,blog_home_url=self.home,
            article_title="Primeiro artigo"),"")

    def test_limit_rejects_invalid_values(self):
        with self.assertRaises(CommerceArticleError):
            from_published_history(self.path,blog_home_url=self.home,
                article_title="Novo",limit=7)


if __name__ == "__main__":
    unittest.main()
