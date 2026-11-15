import hashlib
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import blogger_store_publisher as writer


class TestBloggerStorePublisher(unittest.TestCase):
    def setUp(self):
        self.profile = writer.load_commercial_profile(ROOT / "profiles/cadeira_certa_commercial_safe.json")
        self.catalog = {"blog_id": self.profile["target"]["blog_id"],
                        "page_id": self.profile["store"]["page_id"],
                        "store_url": writer.store_url(self.profile), "count": 4,
                        "products": [
                            {"item_id": str(i), "title": "Oferta sintética",
                             "price": "100.25", "category": category["name"],
                             "offer_link": "https://s.shopee.com.br/fixture",
                             "image": "https://img.susercontent.com/fixture.jpg"}
                            for i, category in enumerate(self.profile["store"]["categories"], 1)]}

    def test_first_publication_and_later_rotation_preserve_surrounding_html(self):
        content = "<h2>Introdução</h2>" + writer.START + "<p>Preparação</p>" + writer.END + "<p>Rodapé</p>"
        page = {"title": "Loja", "content": content, "updated": "old", "etag": "tag"}
        backend = Mock()

        def request(body=None, **kwargs):
            if body is not None:
                return {}
            return page if backend.request.call_count <= 2 else dict(page, content=backend.request.call_args_list[2].args[0])

        backend.request.side_effect = request
        with TemporaryDirectory() as temp:
            out = Path(temp)
            self.assertEqual(writer.publish(self.profile, self.catalog, backend, out, apply=True)["writes"], 1)
            self.assertTrue((out / "before.json").exists())
        update = backend.request.call_args_list[2]
        self.assertEqual(update.kwargs, {"title": "Loja", "etag": "tag"})
        written = update.args[0]
        self.assertTrue(written.startswith("<h2>Introdução</h2>"))
        self.assertTrue(written.endswith("<p>Rodapé</p>"))
        self.assertNotIn("Preparação", written)
        self.assertEqual(writer.card_ids(written), ["1", "2", "3", "4"])
        self.assertEqual(writer.compose(written, "<p>Nova vitrine</p>", self.profile),
                         "<h2>Introdução</h2>" + writer.START + "\n<p>Nova vitrine</p>\n" + writer.END + "<p>Rodapé</p>")
        backend.verify_public.assert_called_once_with(["1", "2", "3", "4"])

    def test_legacy_scaffold_can_be_replaced_only_with_matching_hash(self):
        scaffold = writer.PRELAUNCH + "<p>Temporário</p>" + writer.START + writer.END + "</section>"
        self.profile["store"]["empty_page_sha256"] = hashlib.sha256(scaffold.encode()).hexdigest()
        self.assertEqual(writer.compose(scaffold, "<p>Nova vitrine</p>", self.profile),
                         writer.START + "\n<p>Nova vitrine</p>\n" + writer.END)
        with self.assertRaisesRegex(writer.WriterError, "PRELAUNCH_CONTENT_CHANGED"):
            writer.compose(scaffold.replace("Temporário", "Editado"), "<p>Nova vitrine</p>", self.profile)

    def test_dry_run_reads_only_and_concurrent_edit_blocks_the_put(self):
        page = {"title": "Loja", "content": writer.START + writer.END, "updated": "a"}
        backend = Mock()
        backend.request.return_value = page
        out = Path("unused")
        self.assertEqual(writer.publish(self.profile, self.catalog, backend, out)["writes"], 0)
        backend.request.assert_called_once_with()
        backend.reset_mock()
        backend.request.side_effect = [page, dict(page, updated="b")]
        with self.assertRaisesRegex(writer.WriterError, "PAGE_CHANGED_BEFORE_WRITE"):
            writer.publish(self.profile, self.catalog, backend, out, apply=True)
        self.assertEqual(backend.request.call_count, 2)

    def test_wrong_catalog_target_is_rejected_without_api_calls(self):
        self.catalog["page_id"] = "9999999999"
        backend = Mock()
        with self.assertRaisesRegex(writer.WriterError, "CATALOG_TARGET_MISMATCH"):
            writer.publish(self.profile, self.catalog, backend, Path("unused"), apply=True)
        backend.request.assert_not_called()
