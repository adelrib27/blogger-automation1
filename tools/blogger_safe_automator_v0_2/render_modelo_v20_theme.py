#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

MARKER = "emporio-revisao-visual-20-modelo-final"
TITLE_TOKEN = "__BLOG_TITLE__"
URL_TOKEN = "__BLOG_URL__"
STYLE_MARKER = "BLOGGER_MODELO_V20_IDENTITY_PALETTE"

PALETTES = {
    "blue": {
        "primary": "#175CD3",
        "header_bg": "#F5F9FF",
        "footer_bg": "#102A43",
    },
    "emerald": {
        "primary": "#0F8A5F",
        "header_bg": "#F2FBF7",
        "footer_bg": "#12372A",
    },
    "plum": {
        "primary": "#7C3AED",
        "header_bg": "#F8F5FF",
        "footer_bg": "#2E1065",
    },
    "terracotta": {
        "primary": "#C65D2E",
        "header_bg": "#FFF7F2",
        "footer_bg": "#4A2418",
    },
    "teal": {
        "primary": "#0F766E",
        "header_bg": "#F0FDFA",
        "footer_bg": "#134E4A",
    },
    "burgundy": {
        "primary": "#A11D33",
        "header_bg": "#FFF5F7",
        "footer_bg": "#4C0519",
    },
    "indigo": {
        "primary": "#4338CA",
        "header_bg": "#F5F5FF",
        "footer_bg": "#1E1B4B",
    },
    "amber": {
        "primary": "#B45309",
        "header_bg": "#FFFBEB",
        "footer_bg": "#451A03",
    },
}

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalize_url(value: str) -> str:
    value = value.strip().rstrip("/")
    return value + "/"


def validate_color(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    value = value.strip().upper()
    if not HEX_RE.fullmatch(value):
        raise SystemExit(f"{name} inválida: use hexadecimal #RRGGBB.")
    return value


def choose_palette(title: str, url: str, requested: str) -> tuple[str, dict[str, str]]:
    if requested != "auto":
        if requested not in PALETTES:
            valid = ", ".join(["auto", *PALETTES.keys()])
            raise SystemExit(f"Paleta inválida. Opções: {valid}")
        return requested, dict(PALETTES[requested])

    names = list(PALETTES.keys())
    digest = hashlib.sha256(f"{title}|{url}".encode("utf-8")).digest()
    idx = int.from_bytes(digest[:4], "big") % len(names)
    name = names[idx]
    return name, dict(PALETTES[name])


def identity_css(primary: str, header_bg: str, footer_bg: str) -> str:
    footer_text = "#F8FAFC"
    footer_muted = "#D5DFEA"
    return f"""
<style type='text/css'>
/* {STYLE_MARKER} */
:root {{
  --ga-brand-primary:{primary};
  --ga-brand-header-bg:{header_bg};
  --ga-brand-footer-bg:{footer_bg};
  --ga-brand-footer-text:{footer_text};
  --ga-brand-footer-muted:{footer_muted};
}}

/* Cabeçalho: mantém a estrutura validada, muda somente a identidade visual. */
.centered-top-container {{
  background:var(--ga-brand-header-bg)!important;
  border-top-color:var(--ga-brand-primary)!important;
}}
.centered-top-container .PageList .selected > a,
.centered-top-container .PageList li.selected > a,
.centered-top-container .PageList .selected a,
.centered-top-container .PageList a:hover {{
  background-color:var(--ga-brand-primary)!important;
  color:#fff!important;
}}

/* Acentos que identificam a marca sem alterar a estrutura. */
.ga-featured-v19-more,
.contact-form-button-submit {{
  background:var(--ga-brand-primary)!important;
}}
.ga-featured-v19-more:hover,
.contact-form-button-submit:hover {{
  filter:brightness(.92)!important;
}}

/* Rodapés: mesma estrutura aprovada, cor própria por blog. */
body:not(.item-view) .ga-home-footer,
body.ga-post-page .ga-post-footer,
body.ga-static-page .ga-static-footer {{
  background:var(--ga-brand-footer-bg)!important;
  border-color:var(--ga-brand-footer-bg)!important;
  color:var(--ga-brand-footer-text)!important;
}}

body:not(.item-view) .ga-home-footer h3,
body:not(.item-view) .ga-home-footer h4,
body:not(.item-view) .ga-home-footer a,
body.ga-post-page .ga-post-footer h3,
body.ga-post-page .ga-post-footer h4,
body.ga-post-page .ga-post-footer a,
body.ga-static-page .ga-static-footer h3,
body.ga-static-page .ga-static-footer h4,
body.ga-static-page .ga-static-footer a {{
  color:var(--ga-brand-footer-text)!important;
}}

body:not(.item-view) .ga-home-footer p,
body:not(.item-view) .ga-home-footer .ga-home-footer-bottom,
body:not(.item-view) .ga-home-footer .ga-home-footer-bottom strong,
body.ga-post-page .ga-post-footer p,
body.ga-post-page .ga-post-footer .ga-home-footer-bottom,
body.ga-post-page .ga-post-footer .ga-home-footer-bottom strong,
body.ga-static-page .ga-static-footer p,
body.ga-static-page .ga-static-footer .ga-static-footer-bottom,
body.ga-static-page .ga-static-footer .ga-static-footer-bottom strong {{
  color:var(--ga-brand-footer-muted)!important;
}}

body:not(.item-view) .ga-home-footer .ga-home-footer-bottom,
body.ga-post-page .ga-post-footer .ga-home-footer-bottom,
body.ga-static-page .ga-static-footer .ga-static-footer-bottom {{
  border-top-color:rgba(255,255,255,.16)!important;
}}

body:not(.item-view) .ga-home-footer a:hover,
body.ga-post-page .ga-post-footer a:hover,
body.ga-static-page .ga-static-footer a:hover {{
  color:#fff!important;
  text-decoration:underline!important;
}}
</style>
""".strip()


def main() -> int:
    p = argparse.ArgumentParser(description="Renderiza o TEMA MODELO V20 para um blog novo com identidade visual própria.")
    p.add_argument("--template-theme", required=True)
    p.add_argument("--blog-title", required=True)
    p.add_argument("--blog-url", required=True)
    p.add_argument("--output-theme", required=True)
    p.add_argument(
        "--palette",
        default="auto",
        choices=["auto", *PALETTES.keys()],
        help="Paleta visual. 'auto' escolhe uma paleta determinística pelo título/URL do blog.",
    )
    p.add_argument("--primary-color", help="Sobrescreve a cor principal. Formato #RRGGBB.")
    p.add_argument("--header-bg", help="Sobrescreve o fundo do cabeçalho. Formato #RRGGBB.")
    p.add_argument("--footer-bg", help="Sobrescreve o fundo do rodapé. Formato #RRGGBB.")
    args = p.parse_args()

    src = Path(args.template_theme).resolve()
    out = Path(args.output_theme).resolve()
    if not src.exists():
        raise SystemExit("Template V20 não encontrado.")

    text = src.read_text(encoding="utf-8")
    if MARKER not in text:
        raise SystemExit(f"Template não contém o marcador V20: {MARKER}")
    if TITLE_TOKEN not in text or URL_TOKEN not in text:
        raise SystemExit("Template não contém os tokens de identidade esperados.")
    if STYLE_MARKER in text:
        raise SystemExit("Template já contém uma paleta renderizada; use o template limpo.")

    title = args.blog_title.strip()
    url = normalize_url(args.blog_url)
    palette_name, palette = choose_palette(title, url, args.palette)

    primary = validate_color(args.primary_color, "primary-color") or palette["primary"]
    header_bg = validate_color(args.header_bg, "header-bg") or palette["header_bg"]
    footer_bg = validate_color(args.footer_bg, "footer-bg") or palette["footer_bg"]

    text = text.replace(TITLE_TOKEN, title)
    text = text.replace(URL_TOKEN + "/", url)
    text = text.replace(URL_TOKEN, url.rstrip("/"))

    if TITLE_TOKEN in text or URL_TOKEN in text:
        raise SystemExit("Renderização incompleta: tokens ainda presentes.")

    if "</head>" not in text:
        raise SystemExit("Elemento </head> não encontrado para inserir identidade visual.")
    text = text.replace("</head>", identity_css(primary, header_bg, footer_bg) + "\n</head>", 1)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    ET.parse(out)

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_THEME_RENDERED",
        "template": str(src),
        "output": str(out),
        "blog_title": title,
        "blog_url": url,
        "size_bytes": out.stat().st_size,
        "sha256": sha256(out),
        "xml_valid": True,
        "marker": MARKER,
        "inherits_posts": False,
        "visual_identity": {
            "palette": palette_name,
            "mode": "auto" if args.palette == "auto" else "explicit_palette",
            "primary": primary,
            "header_bg": header_bg,
            "footer_bg": footer_bg,
            "manual_overrides": {
                "primary": args.primary_color is not None,
                "header_bg": args.header_bg is not None,
                "footer_bg": args.footer_bg is not None,
            },
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
