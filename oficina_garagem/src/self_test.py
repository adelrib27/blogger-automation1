from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from quality_gate import quality  # noqa: E402


def article(text, category="Ferramentas", product="Parafusadeira", topic="Parafusadeira: o que conferir antes de comprar"):
    editorial = "".join([f"<h2>Seção {i}</h2><p>{text} " + ("critério de compra e compatibilidade a conferir no anúncio. " * 25) + "</p>" for i in range(1, 5)])
    link = "https://shopee.com.br/exemplo"
    return {"product": product, "topic": topic, "category": category, "affiliate_link": link, "editorial_html": editorial, "content_html": editorial + f'<p><a href="{link}" rel="nofollow sponsored">Oferta</a></p><p>Link de afiliado.</p>'}


def main():
    good = quality(article("Guia informativo sem especificações inventadas."))
    assert good["status"] == "DRAFT_READY", good
    tested = quality(article("Nós testamos este produto e comprovamos o resultado."))
    assert tested["status"] == "REJECTED" and "alegacao_de_teste_nao_comprovada" in tested["reasons"], tested
    risk = quality(article("Compare materiais e confirme certificações.", category="Segurança e Proteção", product="Óculos de Proteção", topic="Óculos de proteção: como escolher"))
    assert risk["status"] == "HUMAN_REVIEW_REQUIRED", risk
    numeric = quality(article("O equipamento entrega 900 Nm de torque."))
    assert numeric["status"] == "REJECTED", numeric
    print("Self-test Oficina & Garagem: 4/4 OK")


if __name__ == "__main__":
    main()
