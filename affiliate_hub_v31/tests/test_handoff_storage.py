"""C37: envelope privado no R2, nunca autoriza publicação."""
import io
import unittest
from unittest.mock import patch

from affiliate_hub_v31.handoff_storage import (
    HandoffStorageError,persist_private_handoff,read_private_handoff,
)

SITE={"site_key":"novo_blog_real","platform":"blogger",
      "identifier":"1234567890123456","campaign":"campanha_blog",
      "allowed_niches":[],"allowed_source_paths":["home living/furniture"],
      "publish_enabled":False}


class S3Mock:
    def __init__(self):
        self.objects={}
    def put_object(self,*,Bucket,Key,Body,**kwargs):
        self.objects[(Bucket,Key)]=Body
        return {}
    def get_object(self,*,Bucket,Key):
        return {"Body":io.BytesIO(self.objects[(Bucket,Key)])}


class StorageMock:
    bucket="private-r2"
    def __init__(self):
        self.s3=S3Mock()


def report():
    return {
        "mode":"C36_UNIVERSAL_HANDOFF_SAFE","site_registered":True,
        "requires_registration":False,"can_publish":False,
        "publication_calls":0,"platform":"blogger","requested_articles":2,
        "review_candidates":3,"conversion_required_keys":["shopee:1:3"],
        "future_review_plans":[],
        "conversion_review_plans":[{
            "product_key":"shopee:1:3","campaign":"campanha_blog",
            "affiliate_url":None,"can_publish":False}],
        "ready_review_jobs":[{
            "site_key":"novo_blog_real","platform":"blogger",
            "campaign":"campanha_blog","product_key":"shopee:1:2",
            "product":{"productName":"Mesa de madeira","shopId":"1",
                "itemId":"2","productLink":"https://shopee.com.br/product/1/2",
                "imageUrl":"https://cf.shopee.com.br/file/test",
                "offerLink":"https://s.shopee.com.br/campanha-real",
                "sourceModes":["csv_r2_verified_affiliate_cache"]},
            "status":"REVIEW_REQUIRED","publication_allowed":False,
            "editorial_brief":{"proposed_title":"Como escolher mesa",
                              "status":"REVIEW_REQUIRED"}}
        ],
    }


class HandoffStorageTests(unittest.TestCase):
    def setUp(self):
        self.store=StorageMock()
        self.patch=patch("affiliate_hub_v31.handoff_storage.sites",
                         return_value={"novo_blog_real":SITE})
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_saved_verified_and_read_back_only_exact_campaign(self):
        result=persist_private_handoff(self.store,site_key="novo_blog_real",
                                       report=report())
        self.assertTrue(result["saved_and_verified"])
        self.assertEqual(result["review_jobs"],1)
        self.assertEqual(result["publication_calls"],0)
        got=read_private_handoff(self.store,site_key="novo_blog_real")
        self.assertEqual(got["campaign"],"campanha_blog")
        self.assertEqual(got["jobs"][0]["product"]["offerLink"],
                         "https://s.shopee.com.br/campanha-real")
        self.assertFalse(got["publication_allowed"])

    def test_invalid_campaign_or_wrong_link_never_persists(self):
        data=report()
        data["ready_review_jobs"][0]["campaign"]="outra_campanha"
        with self.assertRaises(HandoffStorageError):
            persist_private_handoff(self.store,site_key="novo_blog_real",
                                    report=data)
        self.assertEqual(self.store.s3.objects,{})
        data=report()
        data["ready_review_jobs"][0]["product"]["offerLink"]="https://bad.test/"
        with self.assertRaises(HandoffStorageError):
            persist_private_handoff(self.store,site_key="novo_blog_real",
                                    report=data)

    def test_hypothetical_site_report_is_never_persisted(self):
        data=report()
        data["site_registered"]=False
        with self.assertRaises(HandoffStorageError):
            persist_private_handoff(self.store,site_key="novo_blog_real",
                                    report=data)
        self.assertEqual(self.store.s3.objects,{})

    def test_corrupted_private_object_is_rejected_on_read(self):
        persist_private_handoff(self.store,site_key="novo_blog_real",
                                report=report())
        k=next(key for key in self.store.s3.objects
               if "/versions/" in key[1])
        self.store.s3.objects[k]=b"tampered"
        with self.assertRaises(HandoffStorageError):
            read_private_handoff(self.store,site_key="novo_blog_real")


if __name__=="__main__":
    unittest.main()
