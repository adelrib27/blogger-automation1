"""C69 — testes UNIVERSAIS (não restritos a pets) para Evidence/READY SAFE."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.future_blog_seo import audit_future_article
from affiliate_hub_v31 import universal_evidence_ready as core


NOW = datetime(2026, 11, 19, 19, 0, tzinfo=timezone.utc)
STAMP = "2026-11-19T12:00:00Z"
HOME = "https://exemplo-universal.example/"
OTHER = "https://outro-blog.example/"
KEYS = [f"shopee:111:{i}" for i in range(456, 461)]
TITLES = [
    "Cadeira ergonômica modelo A para trabalho",
    "Cadeira ergonômica modelo B para trabalho",
    "Cadeira ergonômica modelo C para trabalho",
    "Cadeira ergonômica modelo D para trabalho",
    "Cadeira ergonômica modelo E para trabalho",
]
ROUTES = {
    "blogger_novo_exemplo":{
        "site_key":"blogger_novo_exemplo","platform":"blogger",
        "identifier":"123456789012345","campaign":"exemploblogger",
        "allowed_niches":["casa/moveis"],"publish_enabled":False},
    "wordpress_novo_exemplo":{
        "site_key":"wordpress_novo_exemplo","platform":"wordpress",
        "identifier":OTHER,"campaign":"exemplowp",
        "allowed_niches":["casa/moveis"],"publish_enabled":False},
}


def package(index=0, *, name=None, date=STAMP, identity="EXACT_PRODUCT",
            source="https://fabricante-independente.example/ficha/cadeiras",
            authorized=True, status="VERIFIED"):
    key = KEYS[index]
    return {
        "product_key": key,
        "product_title": name or TITLES[index],
        "product_status": status,
        "verified_utc": date,
        "sources": [
            {
                "evidence_id": f"EVID_{index}_{n}",
                "identity_level": identity,
                "product_key": key,
                "source_kind": "external",
                "source_url": source,
                "approved_host": "fabricante-independente.example",
                "review_status": "AUTHORIZED",
                "authorized": authorized,
                "checked_utc": date,
                "claim_type": kind,
                "claim_text": text,
            }
            for n, (kind, text) in enumerate((
                ("dimensions", "As dimensões são verificadas na ficha externa atual."),
                ("material", "O material declarado consta na fonte autorizada."),
            ))
        ],
    }


def seo_report(index=0):
    q = "como escolher cadeira ergonomica para trabalhar"
    html = (
        "<article><h2>Objetivo da compra</h2><p>Critérios</p>"
        "<h2>Verificar medidas</h2><p>Dados do anúncio</p>"
        "<h2>Conclusão</h2><p>Antes da compra confira a ficha</p>"
        '<img src="https://cf.shopee.com.br/file/imagem" '
        'alt="Cadeira ergonômica do anúncio Shopee">'
        '<a href="https://s.shopee.com.br/LinkCampanha" '
        'rel="nofollow sponsored">Ver na Shopee</a>'
        "<p>Este artigo contém link de afiliado e comissão.</p></article>"
    )
    return audit_future_article(
        site_url=HOME,
        article_url=HOME+f"guia-cadeira-{index}/",
        title="Como escolher uma cadeira ergonômica para seu escritório",
        meta_description=(
            "Saiba como comparar cadeiras ergonômicas para trabalhar "
            "com atenção às medidas, conforto, ajustes e condições de compra."
        ),
        primary_query=q,
        intent="buying_guide",
        html_content=html,
        published_posts=[],
        keyword_evidence={
            "source":"serp_research",
            "query":q,
            "observed_utc":"2026-11-19T10:00:00Z",
        },
        cluster_id="cadeiras-ergonomicas",
    )


def candidate(index=0, *, angle=None):
    return {
        "product_key": KEYS[index],
        "keyword": "cadeira ergonomica para trabalhar",
        "angle": angle or f"Comparação das medidas e ajustes do modelo {index}",
        "evidence": package(index),
        "seo_audit": seo_report(index),
        "used_evidence_ids":[f"EVID_{index}_0"],
        "editorial_quality_verified": True,
        "article_title": f"Como escolher cadeira ergonômica modelo {index} para casa",
        "content_html":"<article>" + ("Conteúdo original e confirmado. " * 12) + "</article>",
    }


class EvidenceReadyUniversalTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"catalog.sqlite3"
        self.ready_path=Path(tmp.name)/"ready-lab.sqlite3"
        self.store=core.SQLiteReadyLabStore(self.ready_path)
        self.addCleanup(self.store.close)
        with Catalog(self.path) as cat:
            for key,title in zip(KEYS,TITLES):
                shop,item=key.split(":")[1:]
                with cat.db:
                    cat.db.execute("""
                        INSERT INTO products(
                            product_key, shop_id,item_id,title,description,
                            origin_url,image_url,moderation,moderation_reason,
                            first_source,last_seen_utc
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,shop,item,title,"",
                         f"https://shopee.com.br/product/{shop}/{item}",
                         "https://cf.shopee.com.br/file/foto-real",
                         "eligible","","csv_real","2026-11-19T12:00:00Z"))
                    cat.db.execute("""
                        INSERT INTO product_taxonomy(
                            product_key,category,niche,status,reason,version
                        ) VALUES (?,?,?,?,?,?)
                    """,(key,"casa","moveis","matched","evidence","v31"))
                cat.cache_link(key,"exemploblogger",
                               f"https://s.shopee.com.br/CampanhaBlog{item}")
                cat.cache_link(key,"exemplowp",
                               f"https://s.shopee.com.br/CampanhaWP{item}")
        patcher=patch("affiliate_hub_v31.universal_evidence_ready.sites",
                      return_value=ROUTES)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.site="blogger_novo_exemplo"

    def run_safe(self, rows, *, site=None, budget=None, policy=None, now=NOW):
        with Catalog(self.path) as cat:
            before=cat.stats()
            report=core.safe_refill_preview(
                catalog=cat,site_key=site or self.site,
                candidates=rows,store=self.store,now=now,budget=budget,
                policy=policy or core.UniversalReadyPolicy())
            self.assertEqual(before,cat.stats())  # R2/cat não sofre mutação
        self.assertEqual(report["publication_calls"],0)
        self.assertEqual(report["cms_draft_calls"],0)
        self.assertEqual(report["network_calls"],0)
        self.assertEqual(report["shopee_conversions"],0)
        return report

    def test_evidence_exact_product_two_authorized_claims_one_external(self):
        r=core.evidence_whitelist(package=package(0),
             product_key=KEYS[0],product_title=TITLES[0],now=NOW)
        self.assertEqual(r["fact_count"],2)
        self.assertEqual(r["external_source_count"],1)
        self.assertEqual(r["verified_utc"],STAMP)
        self.assertEqual(len(r["allowed_facts"]),2)

    def test_expired_cache_rejected_and_no_ttl_refresh(self):
        old="2026-11-01T12:00:00Z"
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "evidence_cache_expired"):
            core.evidence_whitelist(package=package(0,date=old),
                product_key=KEYS[0],product_title=TITLES[0],now=NOW)
        r=core.evidence_whitelist(package=package(0),
            product_key=KEYS[0],product_title=TITLES[0],now=NOW)
        self.assertEqual(r["verified_utc"],STAMP)

    def test_similar_product_does_not_transfer_specs(self):
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "evidence_external_source_required"):
            core.evidence_whitelist(
                package=package(0,identity="SIMILAR_PRODUCT"),
                product_key=KEYS[0],product_title=TITLES[0],now=NOW)

    def test_matched_model_does_not_transfer_specs(self):
        with self.assertRaises(core.UniversalReadyError):
            core.evidence_whitelist(
                package=package(0,identity="MATCHED_MODEL"),
                product_key=KEYS[0],product_title=TITLES[0],now=NOW)

    def test_wrong_sku_or_name_rejected(self):
        for data in (package(1),package(0,name="Cadeira totalmente diferente")):
            with self.subTest(data=data["product_key"]), self.assertRaises(
                    core.UniversalReadyError):
                core.evidence_whitelist(
                    package=data,product_key=KEYS[0],
                    product_title=TITLES[0],now=NOW)

    def test_non_verified_product_is_blocked(self):
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "evidence_exact_product_mismatch"):
            core.evidence_whitelist(
                package=package(0,status="REVIEW"),product_key=KEYS[0],
                product_title=TITLES[0],now=NOW)

    def test_unauthorized_external_unsupported_source_rejected(self):
        for change in (
            {"authorized":False},
            {"source":"https://shopee.com.br/product/111/456"},
            {"source":"https://fabricante-independente.example.evil.tld/"},
            {"source":"http://fabricante.example/ficha"},
        ):
            with self.subTest(change=change),self.assertRaises(
                    core.UniversalReadyError):
                core.evidence_whitelist(
                    package=package(0,**change),product_key=KEYS[0],
                    product_title=TITLES[0],now=NOW)

    def test_prohibited_absolute_claims_never_enter_whitelist(self):
        data=package()
        for e in data["sources"]:
            e["claim_text"]="100% seguro e cura tudo com resultado garantido"
        with self.assertRaises(core.UniversalReadyError):
            core.evidence_whitelist(package=data,product_key=KEYS[0],
                                    product_title=TITLES[0],now=NOW)

    def test_future_timestamp_and_naive_clock_fail_closed(self):
        with self.assertRaises(core.UniversalReadyError):
            core.evidence_whitelist(package=package(0,date="2099-01-01T00:00:00Z"),
                                    product_key=KEYS[0],product_title=TITLES[0],now=NOW)
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "timezone_required"):
            core.evidence_whitelist(package=package(0),product_key=KEYS[0],
                product_title=TITLES[0],now=datetime(2026,11,19))

    def test_unknown_credit_balance_never_starts_research(self):
        b=core.SearchBudget()
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "search_budget_closed_or_unknown"):
            b.claim("SEARCH")
        self.assertEqual(b.public_report()["search_calls"],0)

    def test_two_search_three_http_budget_and_stop(self):
        b=core.SearchBudget(credit_balance_confirmed=True)
        b.claim("SEARCH"); b.claim("SEARCH")
        for _ in range(3): b.claim("HTTP")
        for event in ("SEARCH","HTTP"):
            with self.subTest(event=event),self.assertRaisesRegex(
                    core.UniversalReadyError,"budget_exhausted"):
                b.claim(event)
        self.assertEqual(b.public_report()["search_calls"],2)
        self.assertEqual(b.public_report()["http_attempts"],3)

    def test_429_opens_circuit_even_with_remaining_budget(self):
        b=core.SearchBudget(credit_balance_confirmed=True)
        b.claim("SEARCH")
        b.record_429()
        with self.assertRaises(core.UniversalReadyError):
            b.claim("HTTP")
        self.assertTrue(b.public_report()["circuit_open"])
        self.assertEqual(b.public_report()["rate_limit_429"],1)

    def test_budget_telemetry_sanitized_and_only_claims_mocks(self):
        b=core.SearchBudget(credit_balance_confirmed=True)
        b.event("CACHE_HIT")
        b.event("CACHE_MISS")
        b.report_credits(.5)
        report=b.public_report()
        self.assertEqual(report["cache_hits"],1)
        self.assertEqual(report["cache_misses"],1)
        self.assertEqual(report["credits_reported_total"],.5)
        self.assertNotIn("product",str(report).lower())
        self.assertEqual(report["network_calls_executed_by_this_module"],0)

    def test_budget_no_negative_credits_nan_or_bad_policy(self):
        for cost in (-1, True, float("nan"), float("inf")):
            with self.subTest(cost=cost), self.assertRaises(core.UniversalReadyError):
                core.SearchBudget().report_credits(cost)
        for kwargs in ({"min_ready":0},{"candidate_attempt_limit":0},
                       {"max_similarity":1.0},{"candidate_target":21},
                       {"max_http_attempts":101}):
            with self.subTest(kwargs=kwargs),self.assertRaises(core.UniversalReadyError):
                core.UniversalReadyPolicy(**kwargs)

    def test_first_run_fill_three_ready_not_total_article_cap(self):
        b=core.SearchBudget()
        report=self.run_safe([candidate(i) for i in range(5)],budget=b)
        self.assertEqual(report["status"],"BUFFER_HEALTHY")
        self.assertEqual(report["ready_before"],0)
        self.assertEqual(report["ready_after"],3)
        self.assertEqual(report["created"],3)
        self.assertEqual(report["attempted"],3)
        self.assertEqual(b.public_report()["cache_hits"],3)

    def test_second_run_buffer_healthy_skips_generation(self):
        self.run_safe([candidate(i) for i in range(3)])
        report=self.run_safe([candidate(i) for i in range(3,5)])
        self.assertEqual(report["status"],"BUFFER_HEALTHY_NO_REFILL")
        self.assertEqual(report["attempted"],0)
        self.assertEqual(report["created"],0)

    def test_bad_evidence_failover_to_next_without_relaxing(self):
        broken=candidate(0)
        broken["evidence"]=package(0,identity="SIMILAR_PRODUCT")
        report=self.run_safe([broken,candidate(1)])
        self.assertEqual(report["created"],1)
        self.assertEqual(report["ready_after"],1)
        self.assertEqual(report["attempted"],2)
        self.assertEqual(report["status"],"LOW_READY_FAIL_CLOSED")
        self.assertGreater(report["rejected_reasons"][
            "evidence_external_source_required"],0)

    def test_missing_campaign_link_rejected_by_real_catalog(self):
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("DELETE FROM affiliate_links WHERE product_key=? "
                               "AND campaign=?",(KEYS[0],"exemploblogger"))
        report=self.run_safe([candidate(0),candidate(1)])
        self.assertEqual(report["created"],1)
        self.assertIn("CATALOG_OR_CAMPAIGN_NOT_VERIFIED",
                      report["rejected_reasons"])

    def test_catalog_item_under_review_cannot_be_safe_ready(self):
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("UPDATE products SET moderation='review' "
                               "WHERE product_key=?",(KEYS[0],))
        report=self.run_safe([candidate(0)])
        self.assertEqual(report["created"],0)
        self.assertIn("CATALOG_OR_CAMPAIGN_NOT_VERIFIED",
                      report["rejected_reasons"])

    def test_missing_seo_evidence_blocks(self):
        data=candidate(0)
        data["seo_audit"]={"status":"READY_FOR_EDITORIAL_SAFE_REVIEW",
                           "keyword_source_verified":False,"blockers":[]}
        report=self.run_safe([data])
        self.assertEqual(report["created"],0)
        self.assertIn("SEO_SAFE_GATE_REQUIRED",report["rejected_reasons"])

    def test_unapproved_fact_id_never_enters_ready(self):
        data=candidate(0)
        data["used_evidence_ids"]=["EVID_FROM_SIMILAR_MODEL"]
        report=self.run_safe([data])
        self.assertEqual(report["created"],0)
        self.assertIn("FACTS_WHITELIST_VIOLATION",
                      report["rejected_reasons"])

    def test_quality_false_never_enters_ready(self):
        data=candidate(0)
        data["editorial_quality_verified"]=False
        report=self.run_safe([data])
        self.assertEqual(report["created"],0)
        self.assertIn("EDITORIAL_QUALITY_GATE_REQUIRED",
                      report["rejected_reasons"])

    def test_duplicate_product_keyword_angle_blocks(self):
        item=candidate(0)
        first=self.run_safe([item])
        self.assertEqual(first["created"],1)
        duplicate=self.run_safe([item])
        self.assertEqual(duplicate["created"],0)
        self.assertIn("DUPLICATE_PRODUCT_KEYWORD_ANGLE",
                      duplicate["rejected_reasons"])

    def test_cooldown_blocks_different_angle_before_30_days(self):
        self.run_safe([candidate(0)])
        data=candidate(0,angle="Abordagem totalmente distinta: ergonomia e postura")
        data["evidence"]=package(0,date="2026-12-04T12:00:00Z")
        report=self.run_safe([data],now=NOW+timedelta(days=15))
        self.assertEqual(report["created"],0)
        self.assertIn("PRODUCT_COOLDOWN_ACTIVE",report["rejected_reasons"])

    def test_evergreen_after_cooldown_with_distinct_angle_is_not_total_limit(self):
        self.run_safe([candidate(0)])
        data=candidate(0,angle="Abordagem nova: limpeza e conservação da cadeira")
        data["evidence"]=package(0,date="2026-12-20T12:00:00Z")
        report=self.run_safe([data],now=NOW+timedelta(days=31))
        self.assertEqual(report["created"],1)
        self.assertEqual(self.store.ready_count(self.site,"exemploblogger"),2)

    def test_similarity_blocks_synonym_rewrites_even_after_cooldown(self):
        self.run_safe([candidate(0)])
        too_close=candidate(0,angle="Comparação das medidas e ajustes do modelo zero")
        too_close["evidence"]=package(0,date="2027-01-03T12:00:00Z")
        report=self.run_safe([too_close],now=NOW+timedelta(days=45))
        self.assertEqual(report["created"],0)
        self.assertTrue(any(k.startswith("EVERGREEN_") for k in report[
            "rejected_reasons"]))

    def test_persistence_across_independent_sqlite_sessions(self):
        self.run_safe([candidate(0)])
        other=core.SQLiteReadyLabStore(self.ready_path)
        self.addCleanup(other.close)
        self.assertEqual(other.ready_count(self.site,"exemploblogger"),1)
        self.assertEqual(other.ready_count("wordpress_novo_exemplo","exemplowp"),0)

    def test_independent_sites_do_not_share_drafts_campaigns_or_cooldown(self):
        self.run_safe([candidate(0)])
        report=self.run_safe([candidate(0)],site="wordpress_novo_exemplo")
        self.assertEqual(report["created"],1)
        self.assertEqual(self.store.ready_count(self.site,"exemploblogger"),1)
        self.assertEqual(self.store.ready_count("wordpress_novo_exemplo","exemplowp"),1)

    def test_unregistered_site_never_enters_ready(self):
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "registered_draft_only_site_required"):
            self.run_safe([candidate(0)],site="site_nao_registrado")

    def test_candidate_attempt_limit_bounded_with_five_candidate_shortlist(self):
        p=core.UniversalReadyPolicy(candidate_target=2,candidate_attempt_limit=2)
        bad0=candidate(0)
        bad1=candidate(1)
        bad0["seo_audit"]={}
        bad1["seo_audit"]={}
        report=self.run_safe([bad0,bad1,candidate(2)],policy=p)
        self.assertEqual(report["attempted"],2)
        self.assertEqual(report["created"],0)

    def test_bad_input_does_not_make_writer_or_network_call(self):
        with self.assertRaisesRegex(core.UniversalReadyError,
                                    "ready_preview_input_invalid"):
            self.run_safe([candidate(i) for i in range(5)]*21)

    def test_ready_consumption_simulated_locally_not_wordpress_publication(self):
        self.run_safe([candidate(0)])
        fp=core._fingerprint(KEYS[0],candidate(0)["keyword"],candidate(0)["angle"])
        used=self.store.consume_one_lab(site_key=self.site,
            campaign="exemploblogger",fingerprint=fp,now=NOW)
        self.assertTrue(used)
        self.assertEqual(self.store.ready_count(self.site,"exemploblogger"),0)
        self.assertFalse(self.store.consume_one_lab(site_key=self.site,
            campaign="exemploblogger",fingerprint=fp,now=NOW))


if __name__=="__main__":
    unittest.main()
