"""C68 — regressões isoladas de SEO para os PRÓXIMOS blogs, sem rede/posts."""
import unittest

from affiliate_hub_v31 import future_blog_seo as seo


HOME = "https://novosite.example/"
PAGE = HOME + "como-escolher-cadeira-ergonomica/"
QUERY = "cadeira ergonomica para trabalhar"
PILLAR = HOME + "guia-cadeiras-ergonomicas/"
RELATED = HOME + "cadeira-ergonomica-pequenos-espacos/"
UNRELATED = HOME + "como-limpar-geladeira/"
SHOPEE = "https://s.shopee.com.br/OfertaDaCampanha"
IMG = "https://cf.shopee.com.br/file/sku-exato"
META = (
    "Aprenda como selecionar uma cadeira ergonômica para o trabalho, "
    "conferir dimensões e comparar ofertas sem promessas ou avaliações inventadas."
)
HTML = (
    '<article><h2>Qual necessidade?</h2><p>Trabalhar com conforto.</p>'
    '<h2>Medidas e ajustes</h2><p>Comparar medidas reais.</p>'
    '<h2>Como verificar anúncio</h2><p>Conferir dados no vendedor.</p>'
    '<img src="' + IMG + '" alt="Cadeira ergonômica conforme anúncio Shopee">'
    '<a href="' + SHOPEE + '" rel="nofollow sponsored">Ver na Shopee</a>'
    '<p>Este conteúdo contém link de afiliado e comissão.</p></article>'
)
PUBLISHED = [
    {"title": "Guia completo de cadeiras ergonômicas para casa",
     "url": PILLAR, "status": "publish",
     "cluster_id": "cadeiras", "role": "pillar"},
    {"title": "Como selecionar cadeira ergonômica em espaços pequenos",
     "url": RELATED, "status": "live",
     "cluster_id": "cadeiras", "role": "satellite"},
    {"title": "Limpeza de geladeira: cuidados e manutenção",
     "url": UNRELATED, "status": "publish", "cluster_id": "cozinha"},
]
RESEARCH = {
    "source": "serp_research",
    "query": QUERY,
    "observed_utc": "2026-11-19T12:00:00Z",
}


def payload(**changes):
    base = dict(
        site_url=HOME,
        article_url=PAGE,
        title="Como escolher cadeira ergonômica para trabalhar",
        meta_description=META,
        primary_query=QUERY,
        intent="buying_guide",
        html_content=HTML,
        published_posts=PUBLISHED,
        cluster_id="cadeiras",
        keyword_evidence=RESEARCH,
    )
    base.update(changes)
    return base


class FutureBlogSEOTests(unittest.TestCase):
    def test_brand_new_blog_without_posts_has_no_fabricated_links(self):
        result = seo.plan_internal_links(
            site_url=HOME, current_url=PAGE, primary_query=QUERY,
            published_posts=[], cluster_id="cadeiras")
        self.assertEqual(result["status"], "COLD_START_NO_PUBLISHED_ARTICLES")
        self.assertEqual(result["links"], [])
        self.assertEqual(seo.render_related_links(result), "")
        self.assertTrue(result["relink_after_new_pillar_or_satellites"])
        self.assertEqual(result["network_calls"], 0)

    def test_relevance_pillar_first_and_three_real_posts_not_forced(self):
        result = seo.plan_internal_links(
            site_url=HOME, current_url=PAGE, primary_query=QUERY,
            published_posts=PUBLISHED, cluster_id="cadeiras")
        self.assertEqual(result["status"], "RELATED_POSTS_VERIFIED")
        self.assertEqual([x["url"] for x in result["links"]], [PILLAR, RELATED])
        self.assertEqual([x["role"] for x in result["links"]], ["pillar", "related"])
        self.assertEqual(result["verified_published_posts"], 3)
        self.assertEqual(result["related_published_posts"], 2)
        self.assertEqual(result["publication_calls"], 0)

    def test_draft_pending_future_and_foreign_sites_never_selected(self):
        source = [
            {"title": "Cadeiras ergonômicas para trabalhar no escritório",
             "url": HOME+"rascunho/", "status": "draft"},
            {"title": "Como comprar cadeira ergonômica para trabalhar",
             "url": HOME+"pendente/", "status": "pending"},
            {"title": "Cadeira ergonômica com ajuste lombar",
             "url": HOME+"futuro/", "status": "future"},
            {"title": "Como escolher cadeira ergonômica no portal concorrente",
             "url": "https://outro.example/cadeiras/", "status": "publish"},
            {"title": "Cadeira ergonômica para casa",
             "url": HOME+"publicada/", "status": "publish"},
        ]
        result = seo.plan_internal_links(
            site_url=HOME, current_url=PAGE, primary_query=QUERY,
            published_posts=source)
        self.assertEqual(len(result["links"]), 1)
        self.assertEqual(result["links"][0]["url"], HOME+"publicada/")
        self.assertEqual(result["verified_published_posts"], 1)

    def test_unrelated_verified_posts_are_not_filler(self):
        result = seo.plan_internal_links(
            site_url=HOME, current_url=PAGE, primary_query=QUERY,
            published_posts=[PUBLISHED[-1]])
        self.assertEqual(result["status"], "NO_RELEVANT_INTERNAL_POSTS")
        self.assertEqual(result["links"], [])
        self.assertEqual(result["verified_published_posts"], 1)

    def test_self_links_and_duplicates_skipped(self):
        source = PUBLISHED + [
            {"title": "Uma matéria sobre cadeira ergonômica",
             "url": PILLAR, "status": "publish"},
            {"title": "Cadeira ergonômica para trabalhar",
             "url": PAGE, "status": "publish"},
        ]
        result = seo.plan_internal_links(
            site_url=HOME, current_url=PAGE, primary_query=QUERY,
            published_posts=source, cluster_id="cadeiras")
        self.assertEqual(len(result["links"]), 2)

    def test_reject_wrong_domain_and_url_contaminants(self):
        for bad in (
            "http://novosite.example/",
            "https://novosite.example.evil.test/",
            "https://user:password@novosite.example/",
            "https://novosite.example/?m=1",
            "https://novosite.example/#artigo",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(seo.FutureSEOError):
                    seo.plan_internal_links(site_url=bad,
                        current_url=PAGE, primary_query=QUERY, published_posts=[])
        with self.assertRaises(seo.FutureSEOError):
            seo.plan_internal_links(
                site_url=HOME,
                current_url="https://novosite.example.evil.test/artigo/",
                primary_query=QUERY,published_posts=[])

    def test_invalid_link_limits_and_blank_queries_fail_closed(self):
        for limit in (0, True, 7):
            with self.subTest(limit=limit):
                with self.assertRaises(seo.FutureSEOError):
                    seo.plan_internal_links(site_url=HOME,current_url=PAGE,
                                            primary_query=QUERY,published_posts=[],
                                            limit=limit)
        with self.assertRaises(seo.FutureSEOError):
            seo.plan_internal_links(site_url=HOME,current_url=PAGE,
                                    primary_query="a e os",published_posts=[])

    def test_rendered_link_text_is_escaped_and_relevant(self):
        result=seo.plan_internal_links(
            site_url=HOME,current_url=PAGE,primary_query=QUERY,
            published_posts=PUBLISHED,cluster_id="cadeiras")
        markup=seo.render_related_links(result)
        self.assertIn('class="v31-seo-related"',markup)
        self.assertIn(PILLAR,markup)
        self.assertIn("Guia completo de cadeiras",markup)
        self.assertNotIn(UNRELATED,markup)
        self.assertNotIn("clique aqui",markup.lower())
        with self.assertRaises(seo.FutureSEOError):
            seo.render_related_links({"links":[{"url":"javascript:alert(1)",
                "anchor_text":"Cadeira ergonômica útil"}]})

    def test_new_blog_audit_research_and_published_links(self):
        report=seo.audit_future_article(**payload(
            html_content=HTML.replace("</article>",
                '<a href="'+PILLAR+'">Guia completo de cadeiras ergonômicas para casa</a></article>')
        ))
        self.assertEqual(report["status"],"READY_FOR_EDITORIAL_SAFE_REVIEW")
        self.assertEqual(report["blockers"],[])
        self.assertTrue(report["keyword_source_verified"])
        self.assertTrue(report["manual_quality_review_required"])
        self.assertIn("MOBILE_CORE_WEB_VITALS_LCP_INP_CLS",
                      report["technical_not_measured"])
        self.assertEqual(report["publication_calls"],0)

    def test_no_keyword_evidence_cannot_claim_seo_researched(self):
        report=seo.audit_future_article(**payload(keyword_evidence=None))
        self.assertEqual(report["status"],"BLOCKED_SAFE")
        self.assertIn("SEARCH_INTENT_RESEARCH_EVIDENCE_REQUIRED",report["blockers"])

    def test_keyword_research_wrong_query_or_future_dated_rejected(self):
        for evidence in (
            {"source":"keyword_tool","query":"outro assunto",
             "observed_utc":"2026-01-01T12:00:00Z"},
            {"source":"invented","query":QUERY,
             "observed_utc":"2026-01-01T12:00:00Z"},
            {"source":"serp_research","query":QUERY,
             "observed_utc":"2088-01-01T00:00:00Z"},
        ):
            with self.subTest(evidence=evidence):
                report=seo.audit_future_article(
                    **payload(keyword_evidence=evidence))
                self.assertFalse(report["keyword_source_verified"])

    def test_noncommercial_intent_is_rejected(self):
        with self.assertRaisesRegex(seo.FutureSEOError,
                                    "seo_commercial_intent_required"):
            seo.audit_future_article(**payload(intent="local_business"))

    def test_bad_product_alt_and_missing_image_block(self):
        for altered in (
            HTML.replace('alt="Cadeira ergonômica conforme anúncio Shopee"',
                         'alt="foto"'),
            HTML.replace('<img src="'+IMG+'" alt="Cadeira ergonômica conforme anúncio Shopee">',""),
        ):
            with self.subTest(html=altered[-100:]):
                report=seo.audit_future_article(
                    **payload(html_content=altered))
                self.assertEqual(report["status"],"BLOCKED_SAFE")
                self.assertTrue(any("IMAGE" in x for x in report["blockers"]))

    def test_missing_sponsored_rel_blocks(self):
        report=seo.audit_future_article(**payload(
            html_content=HTML.replace('rel="nofollow sponsored"',
                                       'rel="noopener"')))
        self.assertIn("AFFILIATE_SPONSORED_REL_REQUIRED",report["blockers"])

    def test_nonpublished_internal_link_in_article_blocks(self):
        report=seo.audit_future_article(**payload(
            html_content=HTML.replace("</article>",
                '<a href="'+HOME+'rascunho/">Artigo ainda não publicado</a></article>')))
        self.assertIn("INTERNAL_LINK_NOT_VERIFIED_AS_PUBLISHED",report["blockers"])

    def test_public_review_schema_without_evidence_is_blocked(self):
        altered=HTML + '<script type="application/ld+json">{"@type":"Review"}</script>'
        report=seo.audit_future_article(**payload(html_content=altered))
        self.assertIn("UNVERIFIED_REVIEW_SCHEMA_FORBIDDEN",report["blockers"])

    def test_product_schema_is_not_asserted_as_verified(self):
        altered=HTML + '<script type="application/ld+json">{"@type":"Product"}</script>'
        report=seo.audit_future_article(**payload(html_content=altered))
        self.assertIn("PRODUCT_SCHEMA_NEEDS_INDEPENDENT_FACT_CHECK",
                      report["warnings"])

    def test_no_relevant_posts_does_not_force_fake_links(self):
        report=seo.audit_future_article(
            **payload(published_posts=[],cluster_id="cadeiras"))
        self.assertEqual(report["status"],"READY_FOR_EDITORIAL_SAFE_REVIEW")
        self.assertEqual(report["internal_link_plan"]["links"],[])
        self.assertIn("INTERNAL_LINK_COLD_START_OR_NO_RELEVANT_POSTS",
                      report["warnings"])

    def test_seo_length_preferences_are_not_google_ranking_guarantees(self):
        report=seo.audit_future_article(
            **payload(meta_description="Muito curta"))
        self.assertIn("META_DESCRIPTION_LENGTH_EDITORIAL_REVIEW",
                      report["warnings"])
        self.assertEqual(report["status"],"READY_FOR_EDITORIAL_SAFE_REVIEW")

    def test_never_changes_existing_blog_writer_or_makes_network_calls(self):
        report=seo.audit_future_article(**payload())
        self.assertEqual(report["publication_calls"],0)
        self.assertEqual(report["network_calls"],0)
        self.assertNotIn("LIVE_CONFIRMED",str(report))


if __name__ == "__main__":
    unittest.main()
