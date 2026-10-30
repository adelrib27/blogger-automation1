from __future__ import annotations

import html
import os
import re
from datetime import datetime, timezone

from automation import (
    CONFIG_PATH,
    STATE_PATH,
    choose_product,
    create_blogger_post,
    generate_chatgpt_copy,
    load_json,
    parse_float,
    parse_sales,
    prepare_product_image,
    save_json,
)


def fallback_copy(product, query):
    raw = re.sub(r"\s+", " ", str(product.get("productName") or "")).strip()
    cleaned = re.sub(r"(?i)\b(alta qualidade|promo[cç][aã]o|oferta|imperd[ií]vel|original)\b", "", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -–|,")
    words = []
    seen = set()
    for token in cleaned.split():
        key = re.sub(r"\W+", "", token).lower()
        if key and len(key) > 2 and key in seen:
            continue
        if key:
            seen.add(key)
        words.append(token)
    title = " ".join(words).strip()
    if len(title) > 86:
        title = title[:86].rsplit(" ", 1)[0].rstrip(" -–|,:")
    if len(title) < 24:
        title = f"{title}: guia de compra e pontos para conferir"
    title = title[:100]
    description = (
        f"Este produto aparece na Shopee na categoria {query['label']}. "
        "A análise abaixo organiza os dados confirmados da oferta e mostra o que vale conferir antes da compra."
    )
    return {
        "title": title,
        "description": description,
        "model": "fallback-editorial-local",
        "source": "fallback",
    }


def editorial_copy(product, query, config):
    if os.getenv("OPENAI_API_KEY", "").strip():
        try:
            return generate_chatgpt_copy(product, query, config)
        except Exception as exc:
            print(f"Aviso: copy externa indisponível; usando fallback editorial. Motivo: {exc}")
    return fallback_copy(product, query)


def category_checklist(label):
    checks = {
        "Fones": [
            ("Autonomia", "confira a duração informada da bateria e, se houver estojo, quantas recargas adicionais ele oferece."),
            ("Microfone", "se pretende fazer chamadas, procure informações e avaliações específicas sobre a captação de voz."),
            ("Encaixe e conforto", "observe o formato, o peso e comentários de compradores sobre uso prolongado."),
            ("Latência", "para vídeos e jogos, veja se há relatos de atraso entre imagem e som."),
            ("Resistência", "só considere proteção contra água ou suor quando houver indicação clara no anúncio."),
            ("Carregamento", "confirme o tipo de conector, o cabo incluído e o tempo estimado de carga."),
        ],
        "Carregadores": [
            ("Potência", "confirme a potência real anunciada e se ela é compatível com o aparelho que você pretende carregar."),
            ("Protocolos", "verifique se o anúncio informa padrões de carregamento rápido compatíveis com seu dispositivo."),
            ("Conectores", "confira quantidade, tipo e combinação de portas ou pontas do produto."),
            ("Cabo", "veja se acompanha cabo e qual capacidade de potência ou transferência ele suporta."),
            ("Bivolt e tomada", "em fontes de parede, confirme tensão e padrão do plugue antes da compra."),
            ("Segurança", "procure informações do fabricante, certificações e comentários sobre aquecimento durante o uso."),
        ],
        "Celulares": [
            ("Compatibilidade", "confirme medidas, encaixe e modelos de aparelho suportados."),
            ("Fixação", "em suportes e tripés, veja como o produto prende o aparelho e a superfície de apoio."),
            ("Ajustes", "confira os ângulos, alturas ou posições que realmente podem ser regulados."),
            ("Material", "procure a composição informada e avaliações sobre resistência e acabamento."),
            ("Portas e padrões", "em hubs e adaptadores, confirme exatamente quais conexões são oferecidas."),
            ("Uso pretendido", "compare o produto com sua rotina: mesa, carro, moto, gravação, carregamento ou expansão de portas."),
        ],
        "Casa conectada": [
            ("Rede Wi-Fi", "confirme a frequência de rede exigida e os requisitos de instalação."),
            ("Aplicativo", "veja qual app é indicado e se está disponível para seu celular."),
            ("Assistentes", "considere compatibilidade com Alexa ou Google somente quando isso estiver explícito no anúncio."),
            ("Alimentação", "confirme tensão, potência, soquete ou forma de instalação conforme o tipo de produto."),
            ("Instalação", "avalie se a montagem é simples ou se exige conhecimento elétrico profissional."),
            ("Automação", "procure informações sobre rotinas, temporizadores, cenas e compartilhamento com outros usuários."),
        ],
    }
    return checks.get(label, [
        ("Compatibilidade", "confirme se o produto atende ao aparelho, ambiente ou finalidade pretendida."),
        ("Especificações", "leia a ficha completa e compare medidas, materiais, recursos e conteúdo da embalagem."),
        ("Avaliações", "priorize comentários recentes com fotos e relatos de uso real."),
        ("Garantia", "verifique condições de devolução, garantia e suporte do vendedor."),
    ])


def rich_product_html(product, copy, image_info, label):
    title = html.escape(copy["title"])
    intro = html.escape(copy["description"])
    source_name = html.escape(str(product.get("productName") or "").strip())
    shop = html.escape(str(product.get("shopName") or "").strip())
    link = html.escape(str(product.get("offerLink") or "").strip(), quote=True)
    image = html.escape(str(image_info.get("url") or "").strip(), quote=True)
    safe_label = html.escape(label)
    rating = parse_float(product.get("ratingStar"))
    sales = parse_sales(product.get("sales"))

    metrics = []
    if shop:
        metrics.append(f"<li><strong>Loja:</strong> {shop}</li>")
    if rating:
        metrics.append(f"<li><strong>Avaliação informada:</strong> {rating:.1f}/5</li>")
    if sales:
        metrics.append(f"<li><strong>Vendas informadas:</strong> {sales}</li>")
    metrics.append(f"<li><strong>Categoria:</strong> {safe_label}</li>")

    checks = "".join(
        f"<li><strong>{html.escape(name)}:</strong> {html.escape(text)}</li>"
        for name, text in category_checklist(label)
    )

    image_html = ""
    if image:
        image_html = (
            '<div style="margin:0 auto 30px;max-width:760px;text-align:center;">'
            f'<img src="{image}" alt="{title}" loading="lazy" '
            'style="display:block;width:100%;height:auto;max-height:760px;object-fit:contain;'
            'border-radius:18px;background:#f8fafc;" /></div>'
        )

    return f"""
<article class="conecta-achados-produto conecta-achados-artigo-longo" style="max-width:860px;margin:24px auto;padding:0 4px;line-height:1.78;color:#263746;">
  <p style="margin:0 0 14px;font-size:12px;font-weight:700;letter-spacing:.08em;color:#0F8A5F;text-transform:uppercase;">{safe_label}</p>
  {image_html}
  <p style="font-size:19px;line-height:1.8;margin:0 0 22px;">{intro}</p>
  <p style="font-size:17px;margin:0 0 22px;">No Conecta Achados, a proposta não é apenas mostrar um botão de compra. Este artigo organiza as informações disponíveis, explica como interpretar a oferta e destaca o que precisa ser verificado no anúncio antes de tomar uma decisão. Assim, você consegue comparar melhor e evita depender apenas do título promocional do vendedor.</p>

  <div style="margin:26px 0;padding:18px 20px;border-radius:14px;background:#F2FBF7;border:1px solid #d7f0e5;">
    <p style="margin:0 0 8px;font-weight:700;color:#12372A;">Resumo da oferta no momento da consulta</p>
    <ul style="margin:0;padding-left:20px;">{''.join(metrics)}</ul>
  </div>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">O que o anúncio informa sobre este produto?</h2>
  <p style="font-size:17px;margin:0 0 18px;">O nome original recebido pela API da Shopee foi: <strong>{source_name}</strong>. Esse texto é útil para identificar marca, modelo, conexão, potência, capacidade ou compatibilidade quando esses dados aparecem explicitamente, mas títulos de marketplace costumam repetir palavras e misturar termos comerciais. Por isso, nossa análise separa o que está realmente informado do que ainda precisa ser confirmado.</p>
  <p style="font-size:17px;margin:0 0 18px;">Quando uma característica não aparece nos dados recebidos, ela não é tratada como fato. Em vez de inventar uma especificação, indicamos exatamente o que vale procurar na página da oferta e nas avaliações de compradores.</p>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">Para quem este tipo de produto pode fazer sentido?</h2>
  <p style="font-size:17px;margin:0 0 18px;">Produtos da categoria <strong>{safe_label}</strong> podem atender perfis muito diferentes. O ponto principal é comparar a proposta do item com a sua rotina real. Pense onde você pretende usar, com qual aparelho ou ambiente, com que frequência e quais características seriam indispensáveis para você.</p>
  <p style="font-size:17px;margin:0 0 18px;">Essa análise evita comprar apenas porque a oferta parece barata ou bem avaliada. Um produto pode ter boa nota e ainda assim não ser adequado para uma necessidade específica. Compatibilidade e finalidade devem vir antes do impulso de compra.</p>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">O que vale conferir antes de comprar</h2>
  <p style="font-size:17px;margin:0 0 18px;">Use este checklist como etapa obrigatória antes de finalizar o pedido:</p>
  <ul style="font-size:17px;margin:0 0 22px;padding-left:22px;">{checks}</ul>
  <p style="font-size:17px;margin:0 0 18px;">Além disso, compare as fotos oficiais com as imagens enviadas por compradores. Isso ajuda a perceber tamanho, acabamento, acessórios incluídos e possíveis diferenças entre a apresentação do anúncio e o produto recebido.</p>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">Como interpretar avaliação e número de vendas</h2>
  <p style="font-size:17px;margin:0 0 18px;">A nota média é um bom filtro inicial, mas não deve ser usada sozinha. Avaliações recentes geralmente são mais úteis porque refletem o lote atual, o vendedor e as condições mais próximas do momento da compra. Leia comentários positivos e negativos e procure padrões: se várias pessoas mencionam o mesmo ponto, esse relato merece atenção.</p>
  <p style="font-size:17px;margin:0 0 18px;">O número de vendas também ajuda a mostrar que a oferta já teve circulação, mas quantidade não significa automaticamente qualidade. Use vendas e avaliação como sinais complementares, nunca como substitutos da leitura da ficha técnica e dos comentários.</p>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">Compare antes de decidir</h2>
  <p style="font-size:17px;margin:0 0 18px;">Antes de comprar, abra duas ou três alternativas semelhantes e compare os pontos realmente importantes. Veja se outro anúncio oferece especificações mais claras, mais avaliações com fotos, melhor compatibilidade com sua necessidade ou condições de compra mais interessantes. O menor preço nem sempre representa a melhor escolha.</p>
  <p style="font-size:17px;margin:0 0 18px;">Também confira frete, prazo de entrega, política de devolução e reputação do vendedor. Esses fatores fazem parte da experiência de compra tanto quanto o produto em si e podem mudar ao longo do tempo.</p>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">Sobre a loja e a oferta</h2>
  <p style="font-size:17px;margin:0 0 18px;">A oferta consultada estava associada à loja <strong>{shop or 'informada na página da Shopee'}</strong>. Como reputação, estoque, preço, frete e prazo são dados dinâmicos, a página da Shopee deve ser considerada a fonte final no momento da compra.</p>

  <div style="margin:32px 0;text-align:center;">
    <a href="{link}" target="_blank" rel="nofollow sponsored" style="display:inline-block;padding:16px 28px;background:#0F8A5F;color:#ffffff;text-decoration:none;font-weight:700;border-radius:12px;font-size:17px;box-shadow:0 8px 18px rgba(15,138,95,.16);">Ver oferta atual na Shopee →</a>
  </div>

  <h2 style="font-size:26px;line-height:1.3;margin:34px 0 14px;color:#12372A;">Conclusão</h2>
  <p style="font-size:17px;margin:0 0 18px;">Este produto entrou na curadoria do Conecta Achados porque passou pelos filtros configurados da automação, incluindo disponibilidade de link, identificação do item e nota mínima quando informada. Isso não significa aprovação cega: a decisão final continua dependendo da compatibilidade com sua necessidade e das condições atuais da oferta.</p>
  <p style="font-size:17px;margin:0 0 24px;">Nossa recomendação é usar o artigo como ponto de partida, abrir a página da Shopee, confirmar as especificações que realmente importam para você e comparar com alternativas semelhantes. Esse processo costuma ser mais útil do que escolher somente pelo preço ou pelo título do anúncio.</p>

  <div style="margin:30px 0;padding:18px 20px;border-radius:14px;background:#f8fafc;border:1px solid #e5e7eb;">
    <p style="margin:0;font-size:13px;line-height:1.7;color:#5f6b76;"><strong>Transparência:</strong> este conteúdo pode conter link de afiliado. Se você comprar por esse link, o Conecta Achados pode receber uma comissão, sem custo adicional para você. Preço, estoque, frete, avaliações, número de vendas, características e condições podem mudar. Confira sempre os dados atuais diretamente na Shopee.</p>
  </div>
</article>
""".strip()


def main():
    config = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"keyword_cursor": 0, "used_item_ids": [], "history": []})

    expected_blog_id = str(config.get("blog_id") or "").strip()
    runtime_blog_id = os.getenv("BLOGGER_BLOG_ID", expected_blog_id).strip()
    if not expected_blog_id or runtime_blog_id != expected_blog_id:
        raise RuntimeError("BLOGGER_BLOG_ID não corresponde ao Conecta Achados configurado.")
    os.environ["BLOGGER_BLOG_ID"] = expected_blog_id

    mode = os.getenv("CONECTA_PUBLISH_MODE", str(config.get("publish_mode", "draft"))).strip().lower()
    if mode not in {"draft", "publish"}:
        raise RuntimeError("CONECTA_PUBLISH_MODE deve ser draft ou publish.")

    product, query = choose_product(config, state)
    item_id = str(product.get("itemId") or "").strip()
    print("Produto escolhido:", product.get("productName"), "| itemId:", item_id)

    copy = editorial_copy(product, query, config)
    image_info = prepare_product_image(product)
    content = rich_product_html(product, copy, image_info, query["label"])
    result = create_blogger_post(copy["title"], content, query["label"], mode)

    used = [str(item) for item in state.get("used_item_ids", [])]
    if item_id not in used:
        used.append(item_id)
    state["used_item_ids"] = used[-500:]

    history = list(state.get("history", []))
    history.append({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "item_id": item_id,
        "source_product_name": product.get("productName"),
        "seo_title": copy["title"],
        "category": query["label"],
        "keyword": query["keyword"],
        "blogger_post_id": result.get("id"),
        "blogger_status": result.get("status"),
        "blogger_url": result.get("url"),
        "chatgpt_model": copy.get("model"),
        "image_source": image_info.get("source"),
        "mode": mode,
        "article_standard": "long_form_v2",
    })
    state["history"] = history[-1000:]
    save_json(STATE_PATH, state)

    print("VALIDAÇÃO CONECTA ACHADOS: PASSOU")
    print("Padrão editorial: long_form_v2")
    print("Modo:", mode)
    print("Título:", copy["title"])
    print("Categoria:", query["label"])
    print("Blogger post ID:", result.get("id"))
    print("Status Blogger:", result.get("status"))


if __name__ == "__main__":
    main()
