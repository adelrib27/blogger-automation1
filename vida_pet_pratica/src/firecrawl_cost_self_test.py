import json
import os

import evidence_engine as engine


class FakeResponse:
    def __init__(self, doc):
        self.doc = doc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.doc, ensure_ascii=False).encode("utf-8")


def run():
    original_urlopen = engine.urllib.request.urlopen
    original_key = os.environ.get("FIRECRAWL_API_KEY")
    captured = []
    fixture = {"meaningful": True}

    def fake_urlopen(request, timeout=90):
        payload = json.loads(request.data.decode("utf-8"))
        captured.append(payload)
        description = (
            "Produto Teste X100 com estrutura dobrável, ajuste simples e uso indicado conforme as medidas do animal."
            if fixture["meaningful"] else ""
        )
        return FakeResponse({
            "id": "search-self-test",
            "creditsUsed": 2,
            "data": {
                "web": [{
                    "url": "https://shopee.com.br/product/456/123",
                    "title": "Produto Teste X100",
                    "description": description,
                }]
            },
        })

    try:
        os.environ["FIRECRAWL_API_KEY"] = "self-test-key"
        engine.urllib.request.urlopen = fake_urlopen
        item = {
            "itemId": "123",
            "productName": "Produto Teste X100",
            "productLink": "https://shopee.com.br/product/456/123",
            "categories": ["teste"],
            "keywords": ["produto teste"],
        }

        package = engine.build_evidence_package(item, max_results=8, min_external_authorized_sources=1)
        assert package["status"] == "VERIFIED"
        assert package["version"] == "EVIDENCE_ENGINE_V1_3_SEARCH_LEAN"
        assert package["rules"]["firecrawl_search_scrape_results"] is False
        assert package["rules"]["meaningful_search_snippet_required_for_external_claims"] is True
        assert len(captured) == 1
        assert captured[0]["limit"] == 8
        assert captured[0]["sources"] == ["web"]
        assert "scrapeOptions" not in captured[0]
        external = [
            source for source in package["sources"]
            if source.get("source_domain") != "open-api.affiliate.shopee.com.br"
            and source.get("allowed_in_article")
        ]
        assert external
        assert external[0]["identity_level"] == "EXACT_PRODUCT"
        assert external[0]["support_text"]

        captured.clear()
        fixture["meaningful"] = False
        rejected = engine.build_evidence_package(item, max_results=8, min_external_authorized_sources=1)
        assert rejected["status"] == "REJECTED_EVIDENCE"
        assert any(reason.startswith("external_authorized_sources:0<1") for reason in rejected["reasons"])
        assert len(captured) == 2
        assert all("scrapeOptions" not in payload for payload in captured)
    finally:
        engine.urllib.request.urlopen = original_urlopen
        if original_key is None:
            os.environ.pop("FIRECRAWL_API_KEY", None)
        else:
            os.environ["FIRECRAWL_API_KEY"] = original_key

    print(json.dumps({
        "status": "FIRECRAWL_COST_SELF_TEST_PASS",
        "search_only": True,
        "scrape_options_absent": True,
        "meaningful_external_support_required": True,
        "insufficient_snippet_fail_closed": True,
        "wordpress_written": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    run()
