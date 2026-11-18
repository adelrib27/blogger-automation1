"""V31 — Bloco comercial reutilizável por Blogger e WordPress.

Origem exclusivamente R2 (produtos.image_url + affiliate_links por
product_key/campaign) e links internos de posts publicados já verificados.
Não inventa preço, desconto, estoque, reviews nem imagem; não publica posts.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

from .catalog import Catalog, host_allowed
from .routing import sites
from .taxonomy import normalize


class CommerceArticleError(ValueError):
    pass


IMAGE_DOMAINS = frozenset((
    "susercontent.com", "shopee.com.br", "shopeeusercontent.com",
))


def valid_product_photo(url: str) -> bool:
    """Exige HTTPS de CDN Shopee, não URL arbitrária obtida de CSV."""
    if not isinstance(url, str) or not 12 <= len(url) <= 1500:
        return False
    try:
        u = urlsplit(url)
        host = (u.hostname or "").lower().rstrip(".")
        return (u.scheme == "https" and
                not u.username and not u.password and
                u.port in (None, 443) and
                not u.fragment and
                any(host == root or host.endswith("." + root)
                    for root in IMAGE_DOMAINS) and
                u.path not in ("", "/"))
    except ValueError:
        return False


def _single_verified_offer(catalog: Catalog, *, site_key: str,
                           product_key: str,
                           verified_site_route: dict | None = None
                           ) -> tuple[str, str, str]:
    """Confere origem, moderação, catálogo, imagem e campanha EXATA."""
    # Adaptadores já verificam a rota real; não reconsultar outro registry.
    route = verified_site_route if verified_site_route is not None else sites().get(site_key)
    if (not isinstance(route, dict) or
        route.get("site_key") != site_key or
        route.get("platform") not in ("blogger", "wordpress")):
        raise CommerceArticleError("registered_site_required")
    if not isinstance(product_key, str) or not re.fullmatch(
            r"shopee:[0-9]+:[0-9]+", product_key):
        raise CommerceArticleError("product_key_invalid")
    if catalog.for_conversion(product_key) is None:
        raise CommerceArticleError("product_not_approved")
    row = catalog.db.execute("""
        SELECT p.title,p.image_url,p.origin_url
        FROM products p WHERE p.product_key=?
    """, (product_key,)).fetchone()
    if not row or not valid_product_photo(row[1]) or not host_allowed(row[2]):
        raise CommerceArticleError("real_product_photo_or_origin_required")
    affiliate = catalog.cached_link(product_key, route["campaign"])
    if not affiliate or not host_allowed(affiliate, allow_short=True):
        raise CommerceArticleError("exact_campaign_affiliate_link_required")
    return str(row[0]), str(row[1]), affiliate


def product_offer_html(catalog: Catalog, *, site_key: str,
                       product_key: str, topic: str,
                       verified_site_route: dict | None = None) -> str:
    """Foto da URL no CSV, âncora de palavra-chave e CTA para mesma oferta."""
    title, image, affiliate = _single_verified_offer(
        catalog, site_key=site_key, product_key=product_key,
        verified_site_route=verified_site_route)
    if not isinstance(topic, str) or not 3 <= len(topic.strip()) <= 120:
        raise CommerceArticleError("article_topic_invalid")
    # Relevância básica adicional; a escolha editorial não é inferida do link.
    if not normalize(topic) or not normalize(title):
        raise CommerceArticleError("article_topic_invalid")
    # Não usar imagem/CTA de produto de outro assunto apenas por existir link.
    ignored = {"para","como","onde","comprar","melhor","melhores",
               "produto","oferta","guia","sobre","com","sem","uma",
               "mais","novo","nova","este","esse","esta","de","do",
               "da","em","por","dos","das","um","os","as","ou"}
    topic_tokens = {t for t in normalize(topic).split()
                    if len(t) >= 3 and t not in ignored}
    product_tokens = set(normalize(title).split())
    matches = {t for t in topic_tokens
               if t in product_tokens or (t.endswith("s") and
                   t[:-1] in product_tokens)}
    if not matches:
        raise CommerceArticleError("topic_product_mismatch")
    a = html.escape(affiliate, quote=True)
    img = html.escape(image, quote=True)
    name = html.escape(title, quote=True)
    topic_escaped = html.escape(topic.strip(), quote=True)
    key = html.escape(product_key, quote=True)
    attrs = 'rel="nofollow sponsored noopener noreferrer" target="_blank"'
    # Botão em CSS inline simples, compatível com Blogger e WordPress.
    button_style = (
        "display:inline-block;padding:12px 20px;"
        "background-color:#ee4d2d;color:#ffffff;"
        "text-decoration:none;border-radius:6px;font-weight:700;"
    )
    return (
        '<section class="v31-product-offer" data-v31-product-key="' + key + '">'
        '<p><small><strong>Transparência:</strong> este artigo contém link '
        'de afiliado. Podemos receber comissão por compras elegíveis, '
        'sem custo adicional para você.</small></p>'
        '<h2>Exemplo de produto para comparar</h2>'
        '<figure style="text-align:center;margin:20px auto;">'
        '<a href="' + a + '" ' + attrs + '>'
        '<img src="' + img + '" alt="Foto real do anúncio: ' + name + '" '
        'loading="lazy" decoding="async" '
        'style="display:block;max-width:100%;height:auto;margin:0 auto;">'
        '</a>'
        '<figcaption>' + name + ' — imagem do anúncio cadastrado '
        'no catálogo Shopee.</figcaption></figure>'
        '<p>Quer conferir uma opção de <a href="' + a + '" ' + attrs + '>'
        + topic_escaped + '</a>? O item acima é identificado no catálogo '
        'como <strong>' + name + '</strong>. Confira as medidas, '
        'as especificações, o preço atual e a disponibilidade diretamente '
        'no anúncio antes de decidir.</p>'
        '<p style="text-align:center;"><a href="' + a + '" ' + attrs +
        ' style="' + button_style + '">Ver produto na Shopee</a></p>'
        '</section>'
    )


def related_articles_html(links: list[tuple[str, str]], *,
                          blog_home_url: str,
                          current_url: str | None = None) -> str:
    """No máximo seis links INTERNOS já publicados no mesmo host."""
    if not isinstance(links, list) or len(links) > 6:
        raise CommerceArticleError("related_links_invalid")
    try:
        home = urlsplit(blog_home_url)
        if (home.scheme != "https" or not home.hostname or
            home.username or home.password or
            home.port not in (None, 443)):
            raise ValueError()
        hostname = home.hostname.lower().rstrip(".")
    except (ValueError, TypeError, AttributeError):
        raise CommerceArticleError("blog_home_invalid") from None
    entries, seen = [], set()
    for item in links:
        if (not isinstance(item, tuple) or len(item) != 2 or
            not isinstance(item[0], str) or
            not 3 <= len(item[0].strip()) <= 200 or
            not isinstance(item[1], str)):
            raise CommerceArticleError("related_post_invalid")
        title, url = item
        u = urlsplit(url)
        # Blogger: /2026/11/post.html. WordPress: /post-slug/.
        # Conferir o permalink real de um post; não permitir redireções,
        # paths duplos/encodados ou páginas de sistema.
        wp_path = bool(re.fullmatch(
            r"/(?:[a-z0-9][a-z0-9-]{0,119}/){1,6}", u.path, re.I))
        blogger_path = bool(re.fullmatch(
            r"/(?:[a-z0-9][a-z0-9-]{0,119}/){0,5}"
            r"[a-z0-9][a-z0-9-]{0,119}\.html", u.path, re.I))
        if (u.scheme != "https" or
            (u.hostname or "").lower().rstrip(".") != hostname or
            u.username or u.password or u.port not in (None, 443) or
            u.fragment or u.query or not (wp_path or blogger_path)):
            raise CommerceArticleError("related_post_not_same_blog")
        normalized_url = "https://" + hostname + u.path
        if normalized_url in seen or normalized_url == current_url:
            continue
        seen.add(normalized_url)
        entries.append(
            '<li><a href="' + html.escape(normalized_url, quote=True) + '">'
            + html.escape(title.strip(), quote=True) + '</a></li>'
        )
    if not entries:
        return ""
    return (
        '<aside class="v31-related-articles" data-v31-related="1">'
        '<h2>Leia também neste blog</h2>'
        '<ul>' + "".join(entries) + '</ul></aside>'
    )


def enhance_existing_article_html(original: str, *,
                                  offer: str,
                                  related: str = "") -> str:
    """Adiciona blocos antes de </article>, preserva conteúdo original.

    Fail closed em repetição: a execução não duplica CTAs/fotos. Para trocar
    produto, exigir revisão do artigo e atualização deliberada, não auto-edit.
    """
    if not isinstance(original, str) or "</article>" not in original.lower():
        raise CommerceArticleError("article_body_unexpected")
    if 'data-v31-product-key="' in original:
        if offer in original and (not related or related in original):
            return original
        raise CommerceArticleError("existing_commercial_section_requires_review")
    if related and 'data-v31-related="1"' in original:
        raise CommerceArticleError("existing_related_section_requires_review")
    match = list(re.finditer(r"</article\s*>", original, re.I))[-1]
    return original[:match.start()] + "\n" + offer + "\n" + related + (
        "\n" if related else "") + original[match.start():]
