import sqlite3
import unittest
from unittest.mock import patch
from affiliate_hub_v31 import trackable_supply as m

class TrackableSupplyTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.executescript("""
        CREATE TABLE products(product_key TEXT,title TEXT,description TEXT,moderation TEXT,last_seen_utc TEXT);
        CREATE TABLE product_taxonomy(product_key TEXT,category TEXT,niche TEXT,status TEXT);
        CREATE TABLE affiliate_links(product_key TEXT,campaign TEXT);
        """)
        self.route={"site_key":"blogger_test","campaign":"test","allowed_niches":["cozinha/air_fryers"],"publish_enabled":False}
        self.cat=type("Fixture",(),{"db":self.db})()
    def add(self,key,title,desc="",niche="air_fryers",moderation="eligible",campaign=None):
        self.db.execute("INSERT INTO products VALUES(?,?,?,?,?)",(key,title,desc,moderation,"2026-11-27"))
        self.db.execute("INSERT INTO product_taxonomy VALUES(?,?,?,?)",(key,"cozinha",niche,"matched"))
        if campaign:
            self.db.execute("INSERT INTO affiliate_links VALUES(?,?)",(key,campaign))
    def test_discovery_is_not_approval_and_cache_is_campaign_scoped(self):
        self.add("shopee:1:2","Air fryer Mondial AFN40 modelo",campaign="other")
        self.add("shopee:1:3","Air fryer Mondial AFN50 modelo",campaign="test")
        self.add("shopee:1:4","Air fryer Mondial 220v modelo")
        self.add("shopee:1:5","Air fryer Mondial AFN60 modelo",niche="other")
        self.add("shopee:1:6","Air fryer Mondial AFN70 modelo",moderation="review")
        self.db.execute("PRAGMA query_only=ON")
        with patch.object(m,"route_allows_sku",return_value=True):
            x=m.discover(self.cat,self.route,["mondial"])
        self.assertEqual([v["product_key"] for v in x["candidate_sample"]],["shopee:1:3","shopee:1:2"])
        self.assertTrue(x["candidate_sample"][0]["cached_for_exact_campaign"])
        self.assertFalse(x["candidate_sample"][1]["cached_for_exact_campaign"])
        self.assertFalse(x["eligible_for_draft_write"])
        self.assertFalse(any(v["manufacturer_facts_verified"] or v["eligible_for_draft_write"] for v in x["candidate_sample"]))
    def test_scope_guard_and_rejected_source(self):
        self.add("shopee:1:2","Air fryer Mondial AFN40 modelo")
        with patch.object(m,"route_allows_sku",return_value=False):
            self.assertEqual(m.discover(self.cat,self.route,["mondial"])["candidate_sample"],[])
        with self.assertRaises(ValueError):
            m.discover(self.cat,{**self.route,"publish_enabled":True},["mondial"])
    def test_gtin_discovery_is_not_identity_proof(self):
        self.add("shopee:1:2","Air fryer produto de cozinha","EAN: 4006381333931")
        with patch.object(m,"route_allows_sku",return_value=True):
            x=m.discover(self.cat,self.route,["mondial"])
        self.assertTrue(x["candidate_sample"][0]["gtin_checksum_valid"])
        self.assertFalse(x["candidate_sample"][0]["manufacturer_facts_verified"])
