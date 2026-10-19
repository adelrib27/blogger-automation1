from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from category_rotation import CATEGORY_ORDER, initial_state, mark_published, order_items  # noqa: E402
from cta_context import CTA_BUTTON_TEXT, CTA_CONSULT_TEXT, cta_copy_prompt, make_cta_lead  # noqa: E402
from generate_articles import build, make_plan, meta_description, repair_prompt  # noqa: E402


def sample_item(category="Decoração", product="Vaso Decorativo Cerâmica Minimalista para Sala", focus="vaso decorativo"):
    return {
        "id": 1,
        "shopee_item_id": "123456",
        "product": product,
        "category": category,
        "source_keyword": focus,
        "affiliate_link": "https://s.shopee.com.br/exemplo",
        "image_url": "https://cf.shopee.com.br/file/exemplo",
        "rules": {"category_rotation_required": True},
    }


def long_editorial(focus="vaso decorativo", bad_text=""):
    sections = []
    for i in range(1, 6):
        body = (
            f"{focus} pede escolhas coerentes com o espaço disponível e com a rotina da casa. "
            "Antes de escolher uma solução, vale observar proporções do ambiente, circulação, facilidade de limpeza e manutenção. "
            "Também é útil comparar formatos e possibilidades de uso sem presumir características que não estejam confirmadas. "
            "A decisão tende a ficar mais clara quando o leitor considera o que já existe no cômodo e define uma necessidade concreta. "
            "Na dúvida, medidas, materiais e demais detalhes devem ser conferidos no anúncio ou na ficha técnica do modelo escolhido. "
        ) * 2
        if i == 3 and bad_text:
            body += " " + bad_text
        sections.append(f"<h2>Critério prático {i}</h2><p>{body}</p>")
    return "".join(sections)


def plan(title="Como escolher um vaso para valorizar a decoração", keyword="vaso decorativo"):
    return {
        "title": title,
        "keyword": keyword,
        "reader_need": "Escolher um vaso que combine com o espaço sem sobrecarregar a composição do ambiente.",
        "product_connection": "Um vaso decorativo é uma referência relacionada para comparar formato, proporção e acabamento.",
    }


def must_reject(item, p, bad_text, expected_reason):
    article = build(item, p, long_editorial(bad_text=bad_text), enforce=False)
    assert article["quality"]["status"] == "REJECTED", article["quality"]
    assert any(expected_reason in r for r in article["quality"]["reasons"]), article["quality"]


def main():
    tests = 0
    item = sample_item()
    built = build(item, plan(), long_editorial())
    assert built["quality"]["status"] == "DRAFT_READY", built["quality"]; tests += 1
    assert built["topic"] == built["editorial_title"] == built["seo_title"]; tests += 1
    assert built["quality"]["metrics"]["cta_count"] == 2; tests += 1
    assert built["content_html"].count(item["image_url"]) == 2; tests += 1
    assert built["content_html"].count(item["affiliate_link"]) == 4; tests += 1
    assert built["content_html"].count('rel="nofollow sponsored"') == 4; tests += 1
    assert built["content_html"].count(CTA_BUTTON_TEXT) == 2 and built["content_html"].count(CTA_CONSULT_TEXT) == 2; tests += 1

    must_reject(item, plan(), "Nós testamos este produto e comprovamos o resultado.", "alegacao_de_teste"); tests += 1
    must_reject(item, plan(), "O item suporta exatamente 90 kg.", "especificacao_numerica"); tests += 1
    must_reject(item, plan(), "Desligue o disjuntor e conecte os fios da rede elétrica.", "instrucao_domestica_de_alto_risco"); tests += 1
    must_reject(item, plan(), "Este modelo cura dor cervical e melhora a coluna.", "alegacao_medica"); tests += 1
    must_reject(item, plan(), "O material garante durabilidade e proteção.", "alegacao_absoluta"); tests += 1
    must_reject(item, plan(), "Vaso Decorativo Cerâmica Minimalista para Sala é a referência principal.", "titulo_comercial_copiado"); tests += 1

    meta = meta_description(plan())
    assert 120 <= len(meta) <= 155, (len(meta), meta); tests += 1
    parsed = make_plan(item, '{"title":"Como usar vasos sem pesar a decoração da sala","keyword":"vasos na decoração","reader_need":"Equilibrar proporções e circulação no ambiente.","product_connection":"Um vaso decorativo pode servir como referência de comparação."}')
    assert parsed["title"] == "Como usar vasos sem pesar a decoração da sala"; tests += 1
    repair = repair_prompt(item, plan(), long_editorial(), "quality gate: exemplo")
    assert "RASCUNHO BLOQUEADO" in repair and "quality gate: exemplo" in repair; tests += 1

    qwen_raw = '{"lead":"Para quem deseja aplicar essas orientações na decoração, o Vaso Decorativo em Cerâmica é uma opção relacionada disponível para consulta. Confira as especificações do modelo no anúncio para avaliar se ele atende à sua necessidade; você também pode consultar o modelo na Shopee."}'
    lead = make_cta_lead(item, plan(), qwen_raw)
    contextual = build(item, plan(), long_editorial(), cta_lead=lead, cta_generation_mode="qwen3-contextual")
    assert contextual["quality"]["status"] == "DRAFT_READY"; tests += 1

    hype = "Para quem deseja aplicar as dicas, este incrível Vaso Decorativo é uma opção imperdível para sua sala. Confira as especificações do modelo no anúncio para avaliar se ele atende à sua necessidade; você também pode consultar o modelo na Shopee."
    try:
        build(item, plan(), long_editorial(), enforce=False, cta_lead=hype)
        raise AssertionError("CTA promocional deveria ser bloqueado")
    except RuntimeError as exc:
        assert "promocional" in str(exc).casefold(); tests += 1

    state = initial_state()
    rows = [
        {"id": 1, "category": "Cozinha", "opportunity_score": 99},
        {"id": 2, "category": "Decoração", "opportunity_score": 10},
        {"id": 3, "category": "Organização", "opportunity_score": 50},
    ]
    ordered = order_items(rows, state, pending_only=True)
    assert [x["category"] for x in ordered] == ["Decoração", "Organização", "Cozinha"]; tests += 1
    for category in CATEGORY_ORDER:
        state = mark_published(state, category)
    assert state["cycle"] == 2 and state["pending_categories"] == CATEGORY_ORDER; tests += 1

    prompt = cta_copy_prompt(item, plan()).casefold()
    assert "jornalista" in prompt and "tom neutro" in prompt and "consultar o modelo na shopee" in prompt; tests += 1

    print(f"Self-test Casa e Decoração editorial v3: {tests}/{tests} OK")


if __name__ == "__main__":
    main()
