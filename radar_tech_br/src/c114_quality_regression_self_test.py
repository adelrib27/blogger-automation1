"""C114: regressões editoriais 100% offline, sem IA, Shopee ou WordPress."""
import urllib.error
from unittest.mock import patch

from cta_context import cta_block
from generate_articles import build, meta_description, slug_category
from publish_generated import verify_affiliate_destination
from quality_gate import quality
from self_test import item, plan, editorial


def has_reason(article, prefix):
    return any(r.startswith(prefix) for r in quality(article)["reasons"])


def main():
    good = build(item(), plan(), editorial())
    assert good["quality"]["status"] == "DRAFT_READY", good["quality"]
    assert good["content_html"].count('class="og-produto-relacionado"') == 1
    assert good["content_html"].count('class="og-produto-titulo-original"') == 1
    assert good["content_html"].count(item()["affiliate_link"]) == 2
    assert good["content_html"].count("este é um link de afiliado") == 1

    bad = dict(good, meta_description="O leitor precisa de ajuda para comprar.", excerpt="O leitor precisa de ajuda para comprar.")
    assert has_reason(bad, "vazamento_de_prompt")
    bad = dict(good, editorial_html="O leitor busca informações. " + good["editorial_html"])
    assert has_reason(bad, "vazamento_de_prompt")

    bad = dict(good, seo_title="Como escolher um aparelho para comparar diferentes modelos de produtos tecnológicos atuais")
    assert has_reason(bad, "seo_title_tamanho:")
    bad = dict(good, meta_description="Curto", excerpt="Curto")
    assert has_reason(bad, "meta_description_tamanho:")

    bad = dict(good, content_html=good["content_html"] + cta_block(item(), None))
    assert has_reason(bad, "quantidade_cta_invalida:")

    missing = item()
    missing["shopee_item_id"] = ""
    bad = build(missing, plan(), editorial(), enforce=False)
    assert has_reason(bad, "produto_sem_id_shopee")
    missing = item()
    missing["affiliate_link"] = "https://example.com/link"
    bad = build(missing, plan(), editorial(), enforce=False)
    assert has_reason(bad, "link_afiliado_invalido")
    missing = item()
    missing["affiliate_link"] = ""
    bad = build(missing, plan(), editorial(), enforce=False)
    assert has_reason(bad, "link_afiliado_invalido")

    intro = (
        "Antes de escolher um dispositivo é necessário observar compatibilidade com o uso, "
        "dimensões e limitações declaradas na ficha de produto. As funções básicas, as "
        "condições de instalação e as orientações de manutenção precisam ser conferidas "
        "no anúncio original para evitar uma decisão baseada em promessa sem fonte."
    )
    repeated = "<p>" + intro + "</p>" + editorial() + "<h2>Conclusão</h2><p>" + intro + "</p>"
    bad = build(item(), plan(), repeated, enforce=False)
    assert has_reason(bad, "conclusao_repete_introducao")

    assert slug_category("Ar-condicionado") == "tecnologia/ar-condicionado"
    assert slug_category("Moda & Beleza") == ""

    for title in (
        "Como escolher um smartwatch para sua rotina",
        "TVs e Smart TVs: como escolher tamanho e painel",
        "Ar-condicionado portátil vale a pena?",
        "Qual notebook comprar para estudar?",
    ):
        meta = meta_description({"title": title})
        assert 140 <= len(meta) <= 155, (title, meta)
        assert "O leitor" not in meta

    offer = item()
    offer["product_evidence"] = {
        "priceMin": "100.50", "priceMax": "120.00",
        "ratingStar": "4.6", "shopName": "Loja Exemplo",
        "source_date": "2026-11-23"
    }
    card = cta_block(offer, None)
    assert "R$ 100,50" in card and "4.6/5" in card
    assert "Confirme" not in card or "diretamente no anúncio" in card

    with patch("publish_generated.urllib.request.urlopen",
               side_effect=urllib.error.HTTPError(
                   url=offer["affiliate_link"], code=404, msg="Not Found",
                   hdrs=None, fp=None)):
        try:
            verify_affiliate_destination(offer["affiliate_link"])
        except RuntimeError as exc:
            assert "revisão humana" in str(exc)
        else:
            raise AssertionError("Link 404 deveria bloquear publicação")

    print("C114 qualidade: 15 verificações offline OK; nenhum POST remoto.")


if __name__ == "__main__":
    main()
