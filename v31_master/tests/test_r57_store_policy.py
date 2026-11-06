#!/usr/bin/env python3
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import r57_store_policy as gate

def make_html(offset=0):
    blocks=[gate.START,'<section class="ub-store-r56"><h2>LOJA</h2>']
    for cat in gate.EXPECTED_CATS:
        blocks+=['<section class="ub-store-category"><h3>'+cat+'</h3>']
        index=gate.EXPECTED_CATS.index(cat)
        for i in range(4):
            pid=str(1000000 + offset + index*4 + i)
            blocks.append('<article class="ub-product-card" data-item-id="'+pid+'">'
                '<img src="https://cf.shopee.com.br/abc" alt="Imagem de teste"/>'
                '<a href="https://s.shopee.com.br/abc" rel="nofollow sponsored noopener">Ver</a>'
                '<a href="https://s.shopee.com.br/abc" rel="nofollow sponsored noopener">Detalhes</a>'
                '</article>')
        blocks.append('</section>')
    blocks+=['</section>',gate.END]
    return "\n".join(blocks)

def state_for(html):
    return {
    "schema":gate.SCHEMA,"blog_id":gate.BLOG_ID,"page_id":gate.PAGE_ID,"url":gate.STORE_URL,
    "card_count":16,"affiliate_link_count":32,"item_ids":gate.ids(html),
    "html_sha256":gate.validate_store_html(html)["sha256"],
    "rotation_enabled":False, "allow_auto_write":False,
    "guards":{"blogger_page_exact":True,"no_runner_files_write":True,"no_theme_install":True,
            "no_new_post_or_page":True,"public_pass_before_state_update":True}
    }

class TestPolicy(unittest.TestCase):
    def test_seed_baseline_valid(self):
        a=make_html()
        self.assertEqual(gate.validate_store_html(a)["cards"],16)
        self.assertEqual(gate.validate_state(state_for(a))["blog_id"],gate.BLOG_ID)
    def test_no_change(self):
        a=make_html()
        self.assertEqual(gate.decision(a,a,state_for(a))["status"],"R57_NO_CHANGE")
    def test_change_staged_no_writes(self):
        a,b=make_html(),make_html(20)
        self.assertEqual(gate.decision(a,b,state_for(a))["status"],"R57_CANDIDATE_SAFE_NOT_AUTHORIZED")
    def test_reject_unapproved(self):
        a,b=make_html(),make_html(20)
        self.assertEqual(gate.decision(a,b,state_for(a),allow_write=True)["writes"],False)
    def test_require_independent_activation(self):
        a,b=make_html(),make_html(20);s=state_for(a);s["allow_auto_write"]=True
        self.assertEqual(gate.decision(a,b,s,allow_write=True)["status"],"R57_CANDIDATE_READY_ONE_WRITE")
    def test_corrupt_live_page(self):
        a,b=make_html(),make_html(20);s=state_for(a);s["html_sha256"]="0"*64
        with self.assertRaises(gate.GuardError):gate.decision(a,b,s)
    def test_wrong_blog(self):
        s=state_for(make_html());s["blog_id"]="1625257710858445955"
        with self.assertRaises(gate.GuardError):gate.validate_state(s)
    def test_bad_duplicate(self):
        h=make_html().replace('1000001','1000000')
        with self.assertRaises(gate.GuardError):gate.validate_store_html(h)
    def test_bad_aff_link(self):
        h=make_html().replace('https://s.shopee.com.br/abc','https://evil.example/abc',1)
        with self.assertRaises(gate.GuardError):gate.validate_store_html(h)
    def test_bad_active_html(self):
        h=make_html().replace('</section>', '<script>alert(1)</script></section>',1)
        with self.assertRaises(gate.GuardError):gate.validate_store_html(h)
    def test_other_content_preserved(self):
        a=make_html();b=make_html(20);new=gate.replace_managed_region("PREFIX"+a+"SUFFIX",b)
        self.assertTrue(new.startswith("PREFIX"))
        self.assertTrue(new.endswith("SUFFIX"))
        self.assertEqual(gate.ids(new),gate.ids(b))
    def test_dont_allow_missing_marker(self):
        with self.assertRaises(gate.GuardError):
            gate.validate_store_html(make_html().replace(gate.END,""))
    def test_not_accept_zero_price_fabrication(self):
        h=make_html().replace('class="ub-product-card"','class="fake-card"',1)
        with self.assertRaises(gate.GuardError):gate.validate_store_html(h)
    def test_state_after_public_pass(self):
        a,b=make_html(),make_html(20)
        s=gate.make_state(state_for(a),b)
        self.assertEqual(s["item_ids"],gate.ids(b))
        self.assertFalse(s["allow_auto_write"])

if __name__=="__main__":
    unittest.main(verbosity=2)
