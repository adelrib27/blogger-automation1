from html.parser import HTMLParser
from pathlib import Path

import generate_articles as generator
from publication_gate_v2 import GENERATION_POLICY_VERSION, publication_risk_reasons

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "casa_decoracao" / "data" / "editorial_queue_100.json"
GENERATED_DIR = ROOT / "casa_decoracao" / "data" / "generated"

_original_build_article = generator.build_article
_original_prompt_for = generator.prompt_for
_original_expansion_prompt = generator.expansion_prompt

GLOBAL_V2_RULES = """

BLINDAGEM EDITORIAL V2 — REGRAS QUE TÊM PRIORIDADE:
- Não atribua ao produto propriedades antialérgicas, antibacterianas, antissépticas, antimicrobianas, antiácaros ou benefícios para saúde respiratória, sono, dor ou postura.
- Não use frases que insinuem prevenção, tratamento, cura, alívio, proteção clínica ou eliminação de germes, bactérias, vírus ou fungos.
- Não diga nem sugira que nós testamos, usamos, comprovamos ou tivemos experiência prática com o produto.
- Não invente números, faixas ou frequências: medidas, gramatura, capacidade, peso, porcentagem, potência, voltagem, duração, quantidade de lavagens ou periodicidade de cuidados. Se a pauta pede esse tipo de dado, ensine COMO conferir no anúncio, etiqueta, ficha técnica ou manual, sem fornecer um valor não confirmado.
- Não transforme características genéricas da categoria em características confirmadas do produto citado.
- Não faça prescrição de frequência de lavagem, higienização ou troca; remeta às instruções do fabricante quando isso depender de material, uso ou conservação.
- Use somente HTML bem formado. Feche todas as tags e limite o corpo editorial a <p>, <h2>, <h3>, <ul>, <li>, <strong> e <em>, sem atributos, links, tabelas ou estilos.
- Mantenha entre 900 e 1300 palavras e pelo menos 4 H2 distintos e úteis.
"""

ALLOWED_EDITORIAL_TAGS = {"p", "h2", "h3", "ul", "li", "strong", "em"}


class StrictEditorialHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        if tag not in ALLOWED_EDITORIAL_TAGS:
            self.errors.append(f"tag_nao_permitida:{tag}")
            return
        if attrs:
            self.errors.append(f"atributos_nao_permitidos:{tag}")
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.errors.append(f"tag_autofechada_nao_permitida:{tag.casefold()}")

    def handle_endtag(self, tag):
        tag = tag.casefold()
        if tag not in ALLOWED_EDITORIAL_TAGS:
            self.errors.append(f"fechamento_nao_permitido:{tag}")
            return
        if not self.stack:
            self.errors.append(f"fechamento_sem_abertura:{tag}")
            return
        if self.stack[-1] != tag:
            self.errors.append(f"aninhamento_invalido:{self.stack[-1]}->{tag}")
            return
        self.stack.pop()


def validate_editorial_html(fragment):
    parser = StrictEditorialHTMLParser()
    try:
        parser.feed(str(fragment or ""))
        parser.close()
    except Exception as exc:
        raise RuntimeError(f"HTML editorial inválido: {exc}") from exc
    if parser.stack:
        parser.errors.append("tags_sem_fechamento:" + ",".join(parser.stack[-5:]))
    if parser.errors:
        raise RuntimeError("HTML editorial inválido: " + ", ".join(sorted(set(parser.errors))[:8]))


def hardened_prompt_for(item):
    return GLOBAL_V2_RULES + "\n" + _original_prompt_for(item)


def hardened_expansion_prompt(item, draft_html):
    return GLOBAL_V2_RULES + "\n" + _original_expansion_prompt(item, draft_html)


def hardened_build_article(item, raw_html):
    article = _original_build_article(item, raw_html)
    validate_editorial_html(article.get("editorial_html"))
    risks = publication_risk_reasons(article)
    if risks:
        raise RuntimeError("publication risk gate: " + ", ".join(risks))
    article["generation_policy_version"] = GENERATION_POLICY_VERSION
    article["quality_gate_version"] = 2
    article["last_error"] = ""
    return article


def migrate_old_automated_drafts():
    queue = generator.load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    migrated = 0

    for item in items:
        if item.get("status") != "WORDPRESS_DRAFT":
            continue
        item_id = int(item.get("id") or 0)
        if not item_id:
            continue
        article_path = GENERATED_DIR / f"{item_id:03d}.json"
        article = generator.load_json(article_path, {})
        if int(article.get("generation_policy_version") or 0) == GENERATION_POLICY_VERSION:
            continue

        item["status"] = "QUARANTINE"
        item["generation_attempts"] = 0
        item["last_error"] = "migração automática: rascunho anterior ao gate v2; regeneração obrigatória"
        migrated += 1

    if migrated:
        queue["items"] = items
        generator.save_json(QUEUE_PATH, queue)
        print(f"Migração gate v2: {migrated} rascunho(s) antigo(s) enviados para regeneração segura.")


def recover_transient_rate_limits():
    queue = generator.load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    recovered = 0

    for item in items:
        error = str(item.get("last_error") or "").casefold()
        if "429" not in error and "too many requests" not in error:
            continue
        if item.get("status") not in {"QUARANTINE", "BLOCKED"}:
            continue

        # Erro 429 é limitação transitória do provedor, não falha editorial.
        # Não deve consumir as três tentativas editoriais nem bloquear a pauta.
        item["status"] = "QUARANTINE"
        item["generation_attempts"] = 0
        item["last_error"] = "limite temporário 429 do provedor de IA; nova tentativa automática em execução posterior"
        recovered += 1

    if recovered:
        queue["items"] = items
        generator.save_json(QUEUE_PATH, queue)
        print(f"Rate limit transitório: {recovered} pauta(s) preservadas para nova tentativa futura.")


if __name__ == "__main__":
    generator.prompt_for = hardened_prompt_for
    generator.expansion_prompt = hardened_expansion_prompt
    generator.build_article = hardened_build_article
    migrate_old_automated_drafts()
    generator.main()
    recover_transient_rate_limits()
