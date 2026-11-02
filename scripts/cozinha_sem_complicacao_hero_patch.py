#!/usr/bin/env python3
from pathlib import Path

path = Path('blogger_stores/src/cozinha_sem_complicacao_store.py')
text = path.read_text(encoding='utf-8')
old = '''base.render_store = render_store
base.hero_css = hero_css

IDENTITY_REPLACEMENTS = [
'''
new = '''def build_hero(data: dict) -> list[str]:
    c = data.get("categories") or {}
    eletro = c["Eletroportateis"]
    panelas = c["Panelas & Coccao"]
    organizacao = c["Organizacao & Pia"]
    cafe = c["Cafe & Bebidas"]
    utensilios = c["Utensilios & Preparo"]
    groups = [
        ("Eletroportáteis e cocção em destaque", [(eletro[0], "Eletroportateis"), (eletro[1], "Eletroportateis"), (panelas[0], "Panelas & Coccao"), (panelas[1], "Panelas & Coccao")]),
        ("Organização, café e bebidas", [(organizacao[0], "Organizacao & Pia"), (organizacao[1], "Organizacao & Pia"), (cafe[0], "Cafe & Bebidas"), (cafe[1], "Cafe & Bebidas")]),
        ("Utensílios para preparar melhor", [(utensilios[0], "Utensilios & Preparo"), (utensilios[1], "Utensilios & Preparo"), (utensilios[2], "Utensilios & Preparo"), (utensilios[3], "Utensilios & Preparo")]),
    ]
    slides = []
    for idx, (title, items) in enumerate(groups):
        prefix = hero_css() if idx == 0 else ""
        cards = ''.join(base.hero_card(product, category) for product, category in items)
        slides.append(prefix + f'<div class="blh-card"><strong>{base.esc(title)}</strong><div class="blh-grid">{cards}</div></div>')
    return slides


base.render_store = render_store
base.hero_css = hero_css
base.build_hero = build_hero

IDENTITY_REPLACEMENTS = [
'''
if text.count(old) != 1:
    raise SystemExit(f'HERO_PATCH_FAIL: esperado 1 bloco base, encontrado {text.count(old)}')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('COZINHA_HERO_PATCH_PASS: hero 12 adaptado às cinco categorias da Cozinha')
