from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from quality_gate import quality  # noqa: E402
from generate_articles import build  # noqa: E402


def article(text, category="Ferramentas", product="Parafusadeira", topic="Parafusadeira: o que conferir antes de comprar", focus="parafusadeira"):
    editorial = "".join([f"<h2>Seção {i}</h2><p>{text} " + (f"{focus} critério de compra e compatibilidade a conferir no anúncio. " * 25) + "</p>" for i in range(1, 5)])
    link = "https://shopee.com.br/exemplo"
    return {
        "product": product,
        "topic": topic,
        "category": category,
        "affiliate_link": link,
        "seo_title": "Parafusadeira: o que conferir antes de comprar",
        "meta_description": "Veja critérios práticos para comparar o produto, conferir compatibilidade, limitações, especificações e informações do anúncio antes de decidir pela compra.",
        "focus_keyword": focus,
        "editorial_html": editorial,
        "content_html": editorial + f'<p><a href="/category/ferramentas/">Mais guias</a></p><p><a href="{link}" rel="nofollow sponsored">Oferta</a></p><p>Link de afiliado.</p>'
    }


def main():
    good = quality(article("Guia informativo sem especificações inventadas."))
    assert good["status"] == "DRAFT_READY", good

    tested = quality(article("Nós testamos este produto e comprovamos o resultado."))
    assert tested["status"] == "REJECTED" and "alegacao_de_teste_nao_comprovada" in tested["reasons"], tested

    risk = quality(article("Compare materiais e confirme certificações.", category="Segurança e Proteção", product="Óculos de Proteção", topic="Óculos de proteção: como escolher", focus="oculos de protecao"))
    assert risk["status"] == "HUMAN_REVIEW_REQUIRED", risk

    numeric = quality(article("O equipamento entrega 900 Nm de torque."))
    assert numeric["status"] == "REJECTED" and any(x.startswith("especificacao_numerica_nao_confirmada") for x in numeric["reasons"]), numeric

    dangerous = quality(article("Levante o veículo e depois faça a inspeção."))
    assert dangerous["status"] == "REJECTED" and "instrucao_procedimental_de_alto_risco" in dangerous["reasons"], dangerous

    item = {
        "id": 1,
        "product": "Parafusadeira sem fio com maleta",
        "topic": "Parafusadeira sem fio: o que conferir antes de comprar",
        "category": "Ferramentas",
        "source_keyword": "parafusadeira",
        "affiliate_link": "https://shopee.com.br/exemplo",
        "rules": {"safety_review": False}
    }
    raw = "".join([
        f"<h2>Critério {i}</h2><p>Parafusadeira deve ser comparada conforme a necessidade. " +
        ("Confira no anúncio compatibilidade, acessórios inclusos, ergonomia e limitações antes da compra. " * 24) +
        "</p>" for i in range(1, 5)
    ])
    built = build(item, raw)
    assert built["quality"]["status"] == "DRAFT_READY", built["quality"]
    assert "nofollow sponsored" in built["content_html"] and "/category/ferramentas/" in built["content_html"]

    print("Self-test Oficina & Garagem: 6/6 OK")


if __name__ == "__main__":
    main()
