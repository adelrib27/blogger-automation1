from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generate_articles import build, make_plan, meta_description, slug_category  # noqa: E402
from publish_generated import media_alt_text  # noqa: E402


def item(category="Tecnologia", product="Smartwatch com monitoramento e tela digital", keyword="smartwatch"):
    return {
        "id": 1,
        "slot": "08:00",
        "shopee_item_id": "123",
        "product": product,
        "category": category,
        "source_keyword": keyword,
        "affiliate_link": "https://s.shopee.com.br/exemplo",
        "image_url": "https://cf.shopee.com.br/file/exemplo",
        "rules": {"featured_image_required": True},
    }


def plan(title="Como escolher um smartwatch para sua rotina", keyword="escolher smartwatch"):
    return {
        "title": title,
        "keyword": keyword,
        "reader_need": "Entender os critérios mais importantes antes de escolher um smartwatch para a rotina.",
        "product_connection": "Um smartwatch é uma opção relacionada para comparar recursos e adequação ao uso.",
    }


def editorial(keyword="escolher smartwatch", bad=""):
    sections = []
    for i in range(1, 6):
        body = (
            f"{keyword} exige observar a necessidade real, o contexto de uso e os critérios que mudam a experiência cotidiana. "
            "Antes da compra, vale comparar funções relevantes, limitações, compatibilidade declarada e informações confirmadas no anúncio ou manual. "
            "A escolha deve considerar o perfil de uso, facilidade de operação, manutenção e características que façam sentido para cada pessoa. "
            "Também é importante separar promessas comerciais de dados verificáveis e evitar decidir apenas por uma especificação isolada. "
        ) * 3
        if i == 3 and bad:
            body += " " + bad
        sections.append(f"<h2>Critério prático {i}</h2><p>{body}</p>")
    return "".join(sections)


def main():
    good = build(item(), plan(), editorial())
    assert good["quality"]["status"] == "DRAFT_READY", good["quality"]
    assert 900 <= good["word_count"] <= 1400
    assert good["content_html"].count('class="og-produto-titulo-original"') == 2
    assert good["content_html"].count(item()["image_url"]) == 2
    assert slug_category("Tecnologia") == "tecnologia"
    assert slug_category("Casa & Decoração") == "casa-decoracao"
    assert slug_category("Cozinha & Utilidades") == "cozinha-utilidades"
    assert slug_category("Ferramentas & Automotivo") == "ferramentas-automotivo"
    assert slug_category("Moda & Beleza") == "moda-beleza"

    alt = media_alt_text(item(product="Produto demonstrativo para imagem destacada"))
    assert alt == "Produto demonstrativo para imagem destacada" and len(alt) <= 180

    no_image = item()
    no_image["image_url"] = ""
    rejected = build(no_image, plan(), editorial(), enforce=False)
    assert rejected["quality"]["status"] == "REJECTED"
    assert "imagem_produto_ausente_ou_invalida" in rejected["quality"]["reasons"]

    fake_test = build(item(), plan(), editorial(bad="Nós testamos este produto e comprovamos o resultado."), enforce=False)
    assert "alegacao_de_teste_nao_comprovada" in fake_test["quality"]["reasons"]

    accessibility = build(item(), plan(), editorial(bad="Pessoas com mobilidade reduzida ou idosos podem se beneficiar porque o produto facilita o acesso."), enforce=False)
    assert "alegacao_de_acessibilidade_nao_sustentada" in accessibility["quality"]["reasons"]

    installation = build(item(), plan(), editorial(bad="O suporte pode ser instalado em paredes laterais do ambiente."), enforce=False)
    assert "instalacao_ou_fixacao_nao_confirmada" in installation["quality"]["reasons"]

    trend = build(item(), plan(), editorial(bad="Esse tipo de produto tem se destacado e é uma opção popular."), enforce=False)
    assert "alegacao_de_popularidade_sem_fonte" in trend["quality"]["reasons"]

    causal = build(item(), plan(), editorial(bad="A solução reduz o tempo gasto na rotina e deixa o uso menos estressante."), enforce=False)
    assert "beneficio_funcional_nao_sustentado" in causal["quality"]["reasons"]

    copied = build(item(), plan(), editorial(bad=item()["product"]), enforce=False)
    assert "titulo_comercial_copiado_no_corpo" in copied["quality"]["reasons"]

    risk = item("Ferramentas & Automotivo", "Torquímetro para manutenção automotiva", "torquimetro")
    risk_plan = plan("Como avaliar ferramentas para manutenção automotiva", "ferramentas manutenção automotiva")
    review = build(risk, risk_plan, editorial("ferramentas manutenção automotiva"), enforce=False)
    assert review["quality"]["status"] == "HUMAN_REVIEW_REQUIRED", review["quality"]

    bad_category = item("Categoria Inválida")
    category_result = build(bad_category, plan(), editorial(), enforce=False)
    assert "categoria_radar_invalida" in category_result["quality"]["reasons"]

    parsed = make_plan(item(), '{"title":"Como escolher um smartwatch para sua rotina","keyword":"escolher smartwatch","reader_need":"Entender os critérios antes da escolha.","product_connection":"Um smartwatch se conecta naturalmente ao tema."}')
    assert parsed["title"] == "Como escolher um smartwatch para sua rotina"

    meta = meta_description(plan())
    assert 110 <= len(meta) <= 160, len(meta)

    print("Self-test Radar Tech BR vNext: 15/15 OK")


if __name__ == "__main__":
    main()
