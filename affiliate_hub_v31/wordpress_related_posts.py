"""Links internos WordPress com URLs de publicações REAIS do histórico.

Compatível com qualquer blog WordPress: sem categorias/nichos fixos.
Histórico precisa guardar post ID e URL retornados por WordPress depois
da publicação. Nada é publicado, nenhum URL é inventado.
"""
from __future__ import annotations

import json
from pathlib import Path

from .article_commerce import CommerceArticleError, related_articles_html
from .taxonomy import normalize


def from_published_history(path: Path | str, *, blog_home_url: str,
                           article_title: str, category: str = "",
                           limit: int = 2) -> str:
    if type(limit) is not int or not 0 <= limit <= 6:
        raise CommerceArticleError("internal_link_limit_invalid")
    if not isinstance(article_title, str) or not article_title.strip():
        raise CommerceArticleError("current_article_title_required")
    file = Path(path)
    if not file.is_file() or file.is_symlink():
        raise CommerceArticleError("publication_history_missing")
    try:
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise CommerceArticleError("publication_history_invalid") from None
    if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):
        raise CommerceArticleError("publication_history_invalid")
    if len(doc["items"]) > 20000:
        raise CommerceArticleError("publication_history_unreasonably_large")
    if limit == 0:
        return ""
    prior_title = normalize(article_title)
    options, seen = [], set()
    for index, post in enumerate(doc["items"]):
        if not isinstance(post, dict):
            raise CommerceArticleError("publication_history_invalid")
        url = post.get("wordpress_url")
        title = post.get("editorial_title")
        post_id = post.get("wordpress_post_id")
        if not url or not title or not post_id:
            continue
        try:
            if int(post_id) <= 0:
                continue
        except (TypeError, ValueError):
            continue
        if normalize(title) == prior_title or url in seen:
            continue
        # O verificador common exige mesmo host, permalink e HTTPS.
        try:
            related_articles_html([(str(title), str(url))],
                                  blog_home_url=blog_home_url)
        except CommerceArticleError:
            continue
        seen.add(url)
        relevance = int(bool(category and
                             normalize(post.get("category", "")) ==
                             normalize(category)))
        options.append((relevance,index,str(title),str(url)))
    # Posts da mesma categoria primeiro; entre eles mais recentes primeiro.
    options.sort(key=lambda p:(-p[0],-p[1],p[2]))
    links=[(t,u) for _relevance,_index,t,u in options[:limit]]
    return related_articles_html(links,blog_home_url=blog_home_url)
