"""C13: file ID cannot overwrite previously generated legacy articles."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.queue_identity import highest_reserved_id


class QueueIdentityTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.queue=self.root/"editorial_queue.json"
        self.generated=self.root/"generated"
        self.generated.mkdir()

    def test_existing_generated_article_overrides_stale_reset_queue_ids(self):
        self.queue.write_text(json.dumps({"items":[{"id":4},{"id":9}]}))
        (self.generated/"001.json").write_text("{}")
        (self.generated/"101.json").write_text("{}")
        self.assertEqual(highest_reserved_id(self.queue,self.generated),101)

    def test_queue_greater_than_generated_keeps_monotonicity(self):
        self.queue.write_text(json.dumps({"items":[{"id":190}]}))
        (self.generated/"008.json").write_text("{}")
        self.assertEqual(highest_reserved_id(self.queue,self.generated),190)

    def test_clean_queue_and_missing_generated_yield_zero(self):
        self.generated.rmdir()
        self.assertEqual(highest_reserved_id(self.queue,self.generated),0)

    def test_untrusted_queue_fails_closed(self):
        self.queue.write_text('{"items":[{"id":"abc"}]}')
        with self.assertRaisesRegex(ValueError,"queue_row_id_invalid"):
            highest_reserved_id(self.queue,self.generated)

    def test_file_symlink_fails_closed(self):
        original=self.root/"external.json"
        original.write_text("{}")
        (self.generated/"002.json").symlink_to(original)
        with self.assertRaisesRegex(ValueError,"generated_file_invalid"):
            highest_reserved_id(self.queue,self.generated)


if __name__=="__main__":
    unittest.main()
