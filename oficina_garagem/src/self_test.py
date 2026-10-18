from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from editorial_normalizer import normalize_editorial  # noqa: E402
from quality_gate import quality  # noqa: E402
from generate_articles import build, make_plan, meta_description, repair_prompt  # noqa: E402


def sample_item(category="Ferramentas", product="Parafusadeira sem fio com maleta", focus="parafusadeira"):
    return {
        "id": 1,
        "product": product,
        "category": category,
        "source_keyword": focus,
        "affiliate_link": "https://shopee.com.br/exemplo",
        "image_url": "https://cf.shopee.com.br/file/exemplo",
        "rules": {"safety_review": category == "Segurança e Proteção"},
    }


def long_editorial(focus="organizar ferramentas", bad_text=""):
    sections = []
    for i in range(1, 6):
        body = (
            f"{focus} exige critérios coerentes com a rotina e o espaço disponível. "
            "A organização deve considerar acesso, separação por função, armazenamento e manutenção da ordem. "
            "Exemplos devem ser adaptados ao contexto de cada pessoa, sem presumir padrões fixos de acesso. "
            "Antes de escolher qualquer solução, vale observar dimensões do ambiente, tipos de itens guardados "
            "e facilidade de devolução ao lugar correto. "
        ) * 3
        if i == 3 and bad_text:
            body += " " + bad_text
        sections.append(f"<h2>Critério editorial {i}</h2><p>{body}</p>")
    return "".join(sections)


def plan(title="Como organizar ferramentas de forma prática e eficiente", keyword="organizar ferramentas"):
    return {
        "title": title,
        "keyword": keyword,
        "reader_need": "Aprender maneiras práticas de organizar ferramentas em garagens e oficinas.",
        "product_connection": "Uma caixa de ferramentas pode ser uma opção relacionada de armazenamento.",
    }


def main():
    item = sample_item()
    built = build(item, plan(), long_editorial())
    good = built["quality"]
    assert good["status"] == "DRAFT_READY", good
    assert built["topic"] == built["editorial_title"] == built["seo_title"]
    assert good["metrics"]["cta_count"] == 2
    assert built["content_html"].count(item["image_url"]) == 2
    assert built["content_html"].count(item["affiliate_link"]) == 2

    tested = build(
        item,
        plan(),
        long_editorial(bad_text="Nós testamos este produto e comprovamos o resultado."),
        enforce=False,
    )
    assert tested["quality"]["status"] == "REJECTED"
    assert "alegacao_de_teste_nao_comprovada" in tested["quality"]["reasons"], tested["quality"]

    risk_item = sample_item(
        category="Segurança e Proteção",
        product="Óculos de Proteção Transparente EPI para Trabalho",
        focus="oculos de protecao",
    )
    risk_plan = plan("Como escolher proteção ocular para diferentes tarefas", "proteção ocular")
    risk = build(risk_item, risk_plan, long_editorial("proteção ocular"), enforce=False)
    assert risk["quality"]["status"] == "HUMAN_REVIEW_REQUIRED", risk["quality"]

    numeric = build(
        item,
        plan(),
        long_editorial(bad_text="O equipamento entrega 900 Nm de torque."),
        enforce=False,
    )
    assert numeric["quality"]["status"] == "REJECTED"
    assert any(x.startswith("especificacao_numerica_nao_confirmada") for x in numeric["quality"]["reasons"]), numeric["quality"]

    dangerous = build(
        item,
        plan(),
        long_editorial(bad_text="Levante o veículo e depois faça a inspeção."),
        enforce=False,
    )
    assert dangerous["quality"]["status"] == "REJECTED"
    assert "instrucao_procedimental_de_alto_risco" in dangerous["quality"]["reasons"], dangerous["quality"]

    frequency = build(
        item,
        plan(),
        long_editorial(bad_text="Ferramentas de uso mais frequente devem ficar na frente, enquanto itens menos usados podem ficar atrás."),
    )
    assert frequency["quality"]["status"] == "DRAFT_READY", frequency["quality"]
    assert "uso mais frequente" not in frequency["editorial_html"].casefold()
    assert "menos usados" not in frequency["editorial_html"].casefold()
    assert "mais acessados na sua rotina" in frequency["editorial_html"].casefold()

    misclassified = build(
        item,
        plan(),
        long_editorial(bad_text="Ferramentas pequenas, como parafusos, pregos e porcas, devem ficar separadas."),
    )
    assert misclassified["quality"]["status"] == "DRAFT_READY", misclassified["quality"]
    assert "fixadores, como parafusos" in misclassified["editorial_html"].casefold()

    absolute = build(
        item,
        plan(),
        long_editorial(bad_text="Uma caixa adequada pode preservar a qualidade dos objetos. Outro critério útil é manter categorias separadas."),
    )
    assert absolute["quality"]["status"] == "DRAFT_READY", absolute["quality"]
    assert "preservar a qualidade" not in absolute["editorial_html"].casefold()
    assert "outro critério útil" in absolute["editorial_html"].casefold()

    copied_title = build(
        item,
        plan(),
        long_editorial(bad_text="Parafusadeira sem fio com maleta é uma opção relacionada para organizar o trabalho."),
        enforce=False,
    )
    assert copied_title["quality"]["status"] == "REJECTED"
    assert "titulo_comercial_copiado_no_corpo" in copied_title["quality"]["reasons"], copied_title["quality"]

    no_image_item = dict(item)
    no_image_item["image_url"] = ""
    no_image = build(no_image_item, plan(), long_editorial())
    assert no_image["quality"]["status"] == "DRAFT_READY", no_image["quality"]

    fake_plan_json = """{
      "title": "Como organizar ferramentas sem desperdiçar espaço",
      "keyword": "organizar ferramentas",
      "reader_need": "Aproveitar melhor o espaço disponível para guardar ferramentas.",
      "product_connection": "Uma caixa de ferramentas pode ser uma opção de armazenamento relacionada."
    }"""
    parsed = make_plan(item, fake_plan_json)
    assert parsed["title"] == "Como organizar ferramentas sem desperdiçar espaço"

    repair = repair_prompt(item, plan(), long_editorial(), "quality gate: titulo_comercial_copiado_no_corpo")
    assert "titulo_comercial_copiado_no_corpo" in repair
    assert "RASCUNHO BLOQUEADO" in repair

    heading = normalize_editorial("<h2>Organize por frequência de uso e tipo</h2><p>Texto neutro.</p>")
    assert "necessidade de acesso" in heading.casefold()
    assert "frequência de uso" not in heading.casefold()

    meta = meta_description(plan())
    assert 110 <= len(meta) <= 160, len(meta)
    assert not meta.rstrip(".").casefold().endswith((" de", " da", " do", " em", " para", " com", " sem")), meta

    print("Self-test Oficina & Garagem editorial contextual v2: 14/14 OK")


if __name__ == "__main__":
    main()
