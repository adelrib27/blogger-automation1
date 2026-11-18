"""Regressão offline da verificação R2; não usa nenhuma credencial."""
import io
import unittest

from affiliate_hub_v31.r2_smoke import smoke
from affiliate_hub_v31.r2_state import R2State


class FakeS3:
    def __init__(self, tamper=False):
        self.objects = {}
        self.tamper = tamper
        self.deleted = 0

    def put_object(self, *, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body

    def get_object(self, *, Bucket, Key):
        value = b"tampered" if self.tamper else self.objects[Key]
        return {"Body": io.BytesIO(value)}

    def delete_object(self, *, Bucket, Key):
        self.deleted += 1
        self.objects.pop(Key, None)


class R2SmokeTests(unittest.TestCase):
    def test_success_and_cleanup(self):
        client=FakeS3()
        self.assertEqual(smoke(R2State(client, "v31-editorial-shopee"), "987654"),
                         "V31_C3_R2_SMOKE_PASS")
        self.assertEqual(client.objects,{})
        self.assertEqual(client.deleted,1)

    def test_tampering_cleans_up(self):
        client=FakeS3(tamper=True)
        with self.assertRaisesRegex(ValueError, "roundtrip_mismatch"):
            smoke(R2State(client, "v31-editorial-shopee"), "987654")
        self.assertEqual(client.objects,{})
        self.assertEqual(client.deleted,1)

    def test_invalid_bucket_or_run_id_does_not_write(self):
        client=FakeS3()
        for bucket,runid in (("other-bucket","12"),("v31-editorial-shopee","../../secret")):
            with self.assertRaises(ValueError):
                smoke(R2State(client,bucket),runid)
        self.assertEqual(client.objects,{})


if __name__ == "__main__":
    unittest.main()
